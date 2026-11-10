#!/usr/bin/env python3
"""Vector store abstraction for the AI Textbook RAG backend.

Single backend: ``PrecomputedIndex``. Loads the committed
``data/index.npy`` + ``data/index.json`` artefacts, which are built once with
``python scripts/build_index.py``.

Loading the precomputed files takes milliseconds, which is what makes the
service viable on Hugging Face's free cpu-basic hardware: embedding the 361
textbook chunks at startup would cost ~30s of CPU on every cold start, and the
HF disk is ephemeral, so a persisted local index would be wiped on rebuild
anyway.

All backends expose the same interface: ``search(vector, top_k)`` returning
``[{"text", "metadata", "distance"}, ...]``, plus ``len()``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

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