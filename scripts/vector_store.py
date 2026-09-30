#!/usr/bin/env python3
"""Vector store abstraction for the AI Textbook RAG backend.

Two interchangeable backends, selected automatically:

* ``MemoryIndex``  - default. Embeddings are built in-process from the committed
  ``docs/`` markdown at startup and held in a NumPy matrix. No external service,
  nothing to provision, and correct on a Hugging Face Space whose disk is
  ephemeral because the index is rebuilt from source on every cold start.
  The textbook is only ~360 chunks, so this costs a few seconds of CPU.

* ``SupabaseIndex`` - opt-in, selected when ``SUPABASE_DB_URL`` (or
  ``SUPABASE_URL`` + ``SUPABASE_SERVICE_KEY``) is set. Keeps the index in
  Supabase pgvector via ``vecs`` so cold starts skip the embedding pass.

Both expose the same interface: ``search(vector, top_k)`` returning
``[{"text", "metadata", "distance"}, ...]``, plus ``len()``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from chunking import Chunk, load_markdown_files

logger = logging.getLogger(__name__)

#: all-MiniLM-L6-v2 emits 384-dimensional vectors.
DEFAULT_EMBEDDING_DIMENSION = 384


def _as_vector(value: Any) -> np.ndarray:
    """Coerce an embedding to a 1-D float32 NumPy array."""
    if hasattr(value, "tolist"):
        value = value.tolist()
    return np.asarray(value, dtype=np.float32).ravel()


def _normalise(matrix: np.ndarray) -> np.ndarray:
    """L2-normalise rows so dot product equals cosine similarity."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class MemoryIndex:
    """In-process cosine-similarity index over the textbook chunks."""

    def __init__(self, chunks: List[Chunk], embeddings) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(f"chunk/embedding mismatch: {len(chunks)} vs {len(embeddings)}")
        if not chunks:
            raise ValueError("cannot build an index from zero chunks")

        self.chunks = list(chunks)
        self.ids = [chunk.record_id for chunk in self.chunks]
        self.texts = [chunk.text for chunk in self.chunks]
        self.metadata = [dict(chunk.metadata) for chunk in self.chunks]
        self.matrix = _normalise(
            np.vstack([_as_vector(e) for e in embeddings]).astype(np.float32)
        )
        logger.info("Built in-memory index: %d chunks x %d dims", *self.matrix.shape)

    def __len__(self) -> int:
        return len(self.chunks)

    def search(self, query_embedding, top_k: int = 5) -> List[Dict[str, Any]]:
        query = _normalise(_as_vector(query_embedding).reshape(1, -1))
        # Cosine similarity in [-1, 1]; convert to distance in [0, 2] so lower
        # is better, matching what Supabase pgvector returns.
        similarity = (self.matrix @ query.T).ravel()
        distance = 1.0 - similarity

        limit = max(1, min(int(top_k), len(self.chunks)))
        # argpartition is O(n); the textbook is small so this stays cheap.
        candidates = np.argpartition(distance, limit - 1)[:limit]
        candidates = candidates[np.argsort(distance[candidates])]

        return [
            {
                "text": self.texts[i],
                "metadata": self.metadata[i],
                "distance": float(distance[i]),
            }
            for i in candidates
        ]


# --------------------------------------------------------------------------- #
# Supabase pgvector backend (optional)
# --------------------------------------------------------------------------- #

def build_connection_string() -> str:
    """Resolve the Postgres DSN that ``vecs`` needs."""
    explicit = (os.getenv("SUPABASE_DB_URL") or "").strip()
    if explicit:
        return explicit

    project_url = (os.getenv("SUPABASE_URL") or "").strip()
    service_key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    region = (os.getenv("SUPABASE_REGION") or "").strip()

    if not project_url or not service_key:
        raise RuntimeError(
            "Set SUPABASE_DB_URL (preferred), or SUPABASE_URL + SUPABASE_SERVICE_KEY."
        )

    ref = project_url.split("//", 1)[-1].split("/", 1)[0]
    if ref.endswith(".supabase.co"):
        ref = ref[: -len(".supabase.co")]
    if not ref:
        raise RuntimeError("Could not parse project reference from SUPABASE_URL")

    if region:
        host = f"aws-0-{region}.pooler.supabase.com"
    else:
        logger.warning(
            "SUPABASE_REGION not set; falling back to direct connection on db.%s. "
            "Set SUPABASE_REGION to use the pooler instead.",
            ref,
        )
        host = f"db.{ref}.supabase.co"

    return f"postgresql://postgres.{ref}:{service_key}@{host}:6543/postgres"


class SupabaseIndex:
    """pgvector-backed index, accessed through ``vecs``."""

    def __init__(self, collection) -> None:
        self.collection = collection

    def __len__(self) -> int:
        return len(self.collection)

    def search(self, query_embedding, top_k: int = 5) -> List[Dict[str, Any]]:
        rows = self.collection.query(
            data=[_as_vector(query_embedding).tolist()],
            limit=max(1, int(top_k)),
            include_value=True,
            include_metadata=True,
        )

        results: List[Dict[str, Any]] = []
        for row in rows or []:
            metadata = dict(row[2] or {})
            results.append({
                # vecs has no document column, so text lives in metadata.
                "text": metadata.pop("text", ""),
                "metadata": metadata,
                "distance": float(row[1]) if len(row) > 1 and row[1] is not None else 0.0,
            })
        return results


def get_collection(dimension: int = DEFAULT_EMBEDDING_DIMENSION):
    """Open (creating if needed) the pgvector collection."""
    import vecs

    name = os.getenv("COLLECTION_NAME", "ai_textbook")
    client = vecs.Client(build_connection_string())

    try:
        return client.get_collection(name)
    except Exception:
        logger.info("Collection '%s' not found - creating", name)
        return client.create_collection(name, dimension)


def upsert_chunks(collection, chunks: List[Chunk], embeddings) -> int:
    """Upsert ``(id, vector, metadata)`` triples into a pgvector collection."""
    records = [
        (chunk.record_id, _as_vector(embedding).tolist(),
         dict(chunk.metadata, text=chunk.text))
        for chunk, embedding in zip(chunks, embeddings)
    ]

    batch_size = 100
    for start in range(0, len(records), batch_size):
        collection.upsert(records[start:start + batch_size])
        logger.info("Upserted %d/%d", min(start + batch_size, len(records)), len(records))

    return len(records)


def clear_collection(collection) -> None:
    """Remove every record so a re-ingest is clean."""
    try:
        collection.delete()
        logger.info("Cleared existing records")
    except Exception:
        logger.warning("Could not clear existing records", exc_info=True)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

def supabase_is_configured() -> bool:
    """True when enough Supabase settings are present to attempt a connection."""
    if os.getenv("SUPABASE_DB_URL", "").strip():
        return True
    return bool(
        os.getenv("SUPABASE_URL", "").strip()
        and os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    )


def build_memory_index(model, docs_dir: Path = Path("docs")) -> MemoryIndex:
    """Chunk, embed and index ``docs_dir`` in memory."""
    chunks = load_markdown_files(docs_dir)
    logger.info("Chunked %d sections from %s", len(chunks), docs_dir)

    logger.info("Embedding %d chunks with '%s'...", len(chunks), os.getenv("EMBEDDING_MODEL"))
    embeddings = model.encode([c.text for c in chunks], batch_size=32, show_progress_bar=True)
    return MemoryIndex(chunks, embeddings)
