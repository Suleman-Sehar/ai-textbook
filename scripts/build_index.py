#!/usr/bin/env python3
"""Precompute textbook chunk embeddings for fast cold starts.

Embeds every chunk under ``docs/`` once and writes two committed artefacts:

    data/index.npy     float32 matrix, (n_chunks, 384), L2-normalised
    data/index.json    chunk ids, text, citation metadata, and provenance

The API loads these instead of embedding 361 chunks on every cold start. This
matters on Render's free tier, which has 0.1 CPU: embedding the textbook takes
~30s there versus well under a second to load the files.

Run this whenever ``docs/`` changes::

    python scripts/build_index.py

Both files are deterministic: the same ``docs/`` and ``EMBEDDING_MODEL`` always
produce the same vectors, so re-running without a content change is a no-op in
practice.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chunking import load_markdown_files

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_index")

DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


def build(docs_dir: Path, index_dir: Path, model_name: str) -> None:
    from embedder import get_embedder

    chunks = load_markdown_files(docs_dir)
    logger.info("Chunked %d sections from %s", len(chunks), docs_dir)

    embedder = get_embedder(model_name)
    logger.info("Embedding %d chunks with '%s' ...", len(chunks), model_name)
    vectors = embedder.embed([c.text for c in chunks])

    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.shape[1] != EMBED_DIM:
        raise RuntimeError(f"expected {EMBED_DIM}-dim vectors, got {matrix.shape[1]}")
    if matrix.shape[0] != len(chunks):
        raise RuntimeError(f"vector count {matrix.shape[0]} != chunk count {len(chunks)}")

    # Store L2-normalised so the query path is a single dot product.
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = (matrix / norms).astype(np.float32)

    index_dir.mkdir(parents=True, exist_ok=True)
    npy_path = index_dir / "index.npy"
    json_path = index_dir / "index.json"

    np.save(npy_path, matrix, allow_pickle=False)

    payload = {
        "embedding_model": model_name,
        "dimension": EMBED_DIM,
        "chunk_count": len(chunks),
        "dtype": "float32",
        "source": str(docs_dir),
        "chunks": [
            {
                "id": chunk.record_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    size_npy = npy_path.stat().st_size / 1024
    size_json = json_path.stat().st_size / 1024
    logger.info("Wrote %s (%.1f KiB)", npy_path, size_npy)
    logger.info("Wrote %s (%.1f KiB)", json_path, size_json)
    logger.info("Total %.1f KiB for %d chunks", size_npy + size_json, len(chunks))

    per_module: dict[str, int] = {}
    for chunk in chunks:
        module = str(chunk.metadata.get("module", "unknown"))
        per_module[module] = per_module.get(module, 0) + 1
    print("\nChunks per module:")
    for module, count in sorted(per_module.items()):
        print(f"  {module}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default=os.getenv("DOCS_DIR", "docs"))
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    parser.add_argument("--model", default=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    docs_dir = Path(args.docs)
    if not docs_dir.exists():
        print(f"ERROR: docs directory '{docs_dir}' does not exist")
        return 1

    build(docs_dir, Path(args.index_dir), args.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())