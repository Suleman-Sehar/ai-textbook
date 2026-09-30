#!/usr/bin/env python3
"""Ingest the AI Textbook markdown into Supabase (pgvector) via ``vecs``.

This is only needed for the **optional** Supabase backend. With no Supabase
variables set, the API builds an in-memory index from ``docs/`` automatically at
startup and this script has nothing to do.

Run it after editing ``docs/`` to refresh a Supabase-backed index without
restarting the Space::

    python -m pip install -r requirements.txt
    python scripts/ingest_rag.py

Note: because the Hugging Face disk is ephemeral, an index built only on the
Space is lost on every rebuild. This script is the way to keep one in Supabase.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Allow `python scripts/ingest_rag.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from chunking import load_markdown_files
from vector_store import (
    DEFAULT_EMBEDDING_DIMENSION,
    clear_collection,
    get_collection,
    supabase_is_configured,
    upsert_chunks,
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_textbook")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DOCS_DIR = Path(os.getenv("DOCS_DIR", "docs"))


def main() -> int:
    if not supabase_is_configured():
        print(
            "ERROR: Supabase is not configured.\n"
            "Set SUPABASE_DB_URL (preferred), or SUPABASE_URL + SUPABASE_SERVICE_KEY, "
            "in .env or the environment.\n"
            "Without Supabase the API uses an in-memory index built from docs/ at "
            "startup and no ingestion step is needed."
        )
        return 1

    if not DOCS_DIR.exists():
        print(f"ERROR: docs directory '{DOCS_DIR}' does not exist")
        return 1

    logger.info("Chunking markdown from %s ...", DOCS_DIR)
    chunks = load_markdown_files(DOCS_DIR)
    md_count = len(list(DOCS_DIR.rglob("*.md")))
    logger.info("Produced %d chunks from %d markdown files", len(chunks), md_count)

    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model '%s' ...", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info("Generating embeddings ...")
    embeddings = model.encode([c.text for c in chunks], batch_size=32, show_progress_bar=True)

    logger.info("Connecting to Supabase ...")
    collection = get_collection(DEFAULT_EMBEDDING_DIMENSION)

    clear_collection(collection)
    written = upsert_chunks(collection, chunks, embeddings)

    logger.info(
        "Ingested %d records; collection '%s' now holds %d vectors",
        written, COLLECTION_NAME, len(collection),
    )

    per_module: dict[str, int] = {}
    for chunk in chunks:
        module = str(chunk.metadata.get("module", "unknown"))
        per_module[module] = per_module.get(module, 0) + 1
    print("\nChunks per module:")
    for module, count in sorted(per_module.items()):
        print(f"  {module}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
