#!/usr/bin/env python3
"""Vector store abstraction for the AI Textbook RAG backend.

Three interchangeable backends, selected automatically in this order:

* ``PrecomputedIndex`` - default. Loads ``data/index.npy`` + ``data/index.json``
  committed to the repo. Loads in milliseconds, which is what makes the service
  viable on Render's free tier (0.1 CPU, where embedding 361 chunks at startup
  would cost ~30s). Rebuild with ``python scripts/build_index.py``.

* ``MemoryIndex`` - fallback. Embeds ``docs/`` in-process at startup when the
  precomputed files are missing. Correct but slow to start.

* ``SupabaseIndex`` - opt-in, selected when ``SUPABASE_DB_URL`` (or
  ``SUPABASE_URL`` + ``SUPABASE_SERVICE_KEY``) is set. Keeps the index in
  Supabase pgvector via ``vecs`` so cold starts skip loading anything.

All three expose the same interface: ``search(vector, top_k)`` returning
``[{"text", "metadata", "distance"}, ...]``, plus ``len()``.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from chunking import Chunk, load_markdown_files

logger = logging.getLogger(__name__)

#: all-MiniLM-L6-v2 emits 384-dimensional vectors.
DEFAULT_EMBEDDING_DIMENSION = 384

DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent / "data"


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


def _to_hits(ids, texts, metadata, order, distances) -> List[Dict[str, Any]]:
    """Assemble search results from sorted index positions."""
    return [
        {
            "text": texts[i],
            "metadata": metadata[i],
            # Cosine distance in [0, 2]; lower is a better match.
            "distance": float(distances[i]),
        }
        for i in order
    ]


class _CosineSearch:
    """Shared cosine-similarity search over a pre-normalised matrix."""

    def __init__(self, matrix: np.ndarray, ids, texts, metadata) -> None:
        self.matrix = matrix
        self.ids = list(ids)
        self.texts = list(texts)
        self.metadata = list(metadata)

    def __len__(self) -> int:
        return self.matrix.shape[0]

    def search(self, query_embedding, top_k: int = 5) -> List[Dict[str, Any]]:
        query = _normalise(_as_vector(query_embedding).reshape(1, -1))
        similarity = (self.matrix @ query.T).ravel()
        distance = 1.0 - similarity

        limit = max(1, min(int(top_k), len(self)))
        # argpartition is O(n); the textbook is small so this stays cheap.
        order = np.argpartition(distance, limit - 1)[:limit]
        order = order[np.argsort(distance[order])]
        return _to_hits(self.ids, self.texts, self.metadata, order, distance)


class PrecomputedIndex(_CosineSearch):
    """Index loaded from the committed ``data/index.*`` artefacts."""

    def __init__(self, index_dir: Path = DEFAULT_INDEX_DIR) -> None:
        npy_path = Path(index_dir) / "index.npy"
        json_path = Path(index_dir) / "index.json"

        if not npy_path.exists() or not json_path.exists():
            raise FileNotFoundError(
                f"Precomputed index not found in '{index_dir}'. "
                "Run: python scripts/build_index.py"
            )

        matrix = np.load(npy_path, allow_pickle=False).astype(np.float32)
        payload = json.loads(json_path.read_text(encoding="utf-8"))

        chunks = payload.get("chunks") or []
        if matrix.shape[0] != len(chunks):
            raise ValueError(
                f"index.npy has {matrix.shape[0]} rows but index.json has {len(chunks)} chunks"
            )

        expected = int(payload.get("dimension", DEFAULT_EMBEDDING_DIMENSION))
        if matrix.shape[1] != expected:
            raise ValueError(f"index.npy has dim {matrix.shape[1]}, expected {expected}")

        ids = [c["id"] for c in chunks]
        texts = [c.get("text", "") for c in chunks]
        metadata = [c.get("metadata") or {} for c in chunks]

        super().__init__(_normalise(matrix), ids, texts, metadata)
        self.model_name = payload.get("embedding_model")
        logger.info(
            "Loaded precomputed index: %d chunks x %d dims (model=%s)",
            matrix.shape[0], matrix.shape[1], self.model_name,
        )

    @classmethod
    def available(cls, index_dir: Path = DEFAULT_INDEX_DIR) -> bool:
        index_dir = Path(index_dir)
        return (index_dir / "index.npy").exists() and (index_dir / "index.json").exists()


class MemoryIndex(_CosineSearch):
    """In-process index built from the markdown at startup."""

    def __init__(self, chunks: List[Chunk], embeddings) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(f"chunk/embedding mismatch: {len(chunks)} vs {len(embeddings)}")
        if not chunks:
            raise ValueError("cannot build an index from zero chunks")

        matrix = np.vstack([_as_vector(e) for e in embeddings]).astype(np.float32)
        super().__init__(
            _normalise(matrix),
            [chunk.record_id for chunk in chunks],
            [chunk.text for chunk in chunks],
            [dict(chunk.metadata) for chunk in chunks],
        )
        logger.info("Built in-memory index: %d chunks x %d dims", *matrix.shape)


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


def build_memory_index(embedder, docs_dir: Path = Path("docs")) -> MemoryIndex:
    """Chunk and embed ``docs_dir`` in memory."""
    chunks = load_markdown_files(docs_dir)
    logger.info("Chunked %d sections from %s", len(chunks), docs_dir)
    embeddings = embedder.embed([c.text for c in chunks])
    return MemoryIndex(chunks, embeddings)
