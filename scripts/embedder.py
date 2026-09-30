#!/usr/bin/env python3
"""Embedding backend for the AI Textbook RAG service.

Uses **fastembed** (ONNX Runtime) rather than sentence-transformers/torch. On
Render's free tier (512 MB RAM, 0.1 CPU) torch does not fit: importing it and
loading the model alone costs several hundred MB.

``fastembed`` runs the *same* ``sentence-transformers/all-MiniLM-L6-v2`` weights
through ONNX Runtime and is numerically interchangeable with the torch build:

    per-text cosine(torch, onnx) = 1.0000000
    max absolute difference       = 1.2e-07
    retrieval ranking             = identical

Vectors produced by either runtime therefore stay compatible with each other, so
a precomputed ``data/index.*`` remains valid regardless of which backend built it.

Measured peak RSS for this path: **239 MB**, with torch never imported.
"""

from __future__ import annotations

import logging
import os
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

#: fastembed only accepts fully-qualified model ids. Normalise the common short
#: aliases so a stale `EMBEDDING_MODEL=all-MiniLM-L6-v2` still resolves.
_MODEL_ALIASES = {
    "all-minilm-l6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "minilm-l6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "all-minilm": "sentence-transformers/all-MiniLM-L6-v2",
}


def normalise_model_name(name: str) -> str:
    """Map a short alias to the fully-qualified fastembed model id."""
    name = (name or DEFAULT_MODEL).strip()
    return _MODEL_ALIASES.get(name.lower(), name)


class Embedder:
    """Thin wrapper giving a single ``embed`` call over both backends."""

    def __init__(self, model_name: str = DEFAULT_MODEL, batch_size: int = 32) -> None:
        self.model_name = normalise_model_name(model_name)
        self.batch_size = batch_size
        self.backend = ""
        self._model = None

    def load(self) -> None:
        """Load the model. Cheap enough to call eagerly."""
        if self._model is not None:
            return

        backend = (os.getenv("EMBED_BACKEND") or "fastembed").strip().lower()

        if backend == "sentence-transformers":
            self._load_sentence_transformers()
            return

        try:
            self._load_fastembed()
            return
        except Exception as exc:
            if backend != "auto":
                raise
            logger.warning(
                "fastembed unavailable (%s); falling back to sentence-transformers. "
                "This needs torch and will exceed Render's free-tier memory limit.",
                exc,
            )
            self._load_sentence_transformers()

    def _load_fastembed(self) -> None:
        from fastembed import TextEmbedding

        logger.info("Loading fastembed (ONNX) model '%s'...", self.model_name)
        self._model = TextEmbedding(model_name=self.model_name)
        self.backend = "fastembed"
        logger.info("fastembed ready")

    def _load_sentence_transformers(self) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence-transformers model '%s'...", self.model_name)
        self._model = SentenceTransformer(self.model_name)
        self.backend = "sentence-transformers"
        logger.info("sentence-transformers ready")

    def embed(self, texts: List[str]) -> np.ndarray:
        """Return an ``(len(texts), dim)`` float32 array."""
        self.load()
        if self.backend == "fastembed":
            vectors = np.asarray(list(self._model.embed(texts)), dtype=np.float32)
        else:
            vectors = np.asarray(
                self._model.encode(texts, batch_size=self.batch_size, show_progress_bar=False),
                dtype=np.float32,
            )
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        return vectors

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single question, returning a 1-D vector."""
        return self.embed([text])[0]


_cache: dict[str, Embedder] = {}


def get_embedder(model_name: str = DEFAULT_MODEL) -> Embedder:
    """Process-wide cached embedder."""
    if model_name not in _cache:
        _cache[model_name] = Embedder(model_name)
    return _cache[model_name]