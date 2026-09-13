#!/usr/bin/env python3
"""
RAG Ingestion Script for Physical AI & Humanoid Robotics Textbook
Chunks content by headings, generates embeddings, stores in Supabase (pgvector).
"""

import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderValueSplitter


@dataclass
class ContentChunk:
    text: str
    metadata: Dict[str, Any]


def load_markdown_files(docs_dir: Path) -> List[ContentChunk]:
    """Load all markdown files and extract frontmatter + content."""
    chunks = []
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
    ]
    splitter = MarkdownHeaderValueSplitter(headers_to_split_on=headers_to_split_on)

    for md_file in docs_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        # Extract frontmatter
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2]
                except yaml.YAMLError:
                    pass

        # Get relative path from docs root
        rel_path = md_file.relative_to(docs_dir)
        module = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        doc_id = frontmatter.get("id", rel_path.stem)
        title = frontmatter.get("title", rel_path.stem)
        sidebar_label = frontmatter.get("sidebar_label", title)

        # Split by headers
        try:
            header_chunks = splitter.split_text(content)
        except Exception:
            header_chunks = [{"page_content": content, "metadata": {}}]

        for i, chunk in enumerate(header_chunks):
            chunk_text = chunk.page_content if hasattr(chunk, "page_content") else str(chunk)
            chunk_meta = chunk.metadata if hasattr(chunk, "metadata") else {}

            # Skip empty chunks
            if not chunk_text.strip():
                continue

            metadata = {
                "source_file": str(rel_path),
                "module": module,
                "doc_id": doc_id,
                "title": title,
                "sidebar_label": sidebar_label,
                "section": chunk_meta.get("h1", "") or chunk_meta.get("h2", "") or chunk_meta.get("h3", "") or "Introduction",
                "subsection": chunk_meta.get("h2", "") or chunk_meta.get("h3", "") or chunk_meta.get("h4", "") or "",
                "chunk_index": i,
            }
            metadata.update(frontmatter)
            chunks.append(ContentChunk(text=chunk_text.strip(), metadata=metadata))

    return chunks


def ingest_to_supabase(chunks: List[ContentChunk]):
    """Ingest chunks into Supabase pgvector table."""
    import vecs

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_textbook")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return 1

    # Connect to Supabase
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    vx = vecs.Client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Create or get collection (table)
    dims = 384  # all-MiniLM-L6-v2 produces 384-dim embeddings
    try:
        collection = vx.get_collection(COLLECTION_NAME)
        print(f"Found existing collection '{COLLECTION_NAME}'")
    except Exception:
        print(f"Creating collection '{COLLECTION_NAME}' with {dims} dimensions...")
        collection = vx.create_collection(
            name=COLLECTION_NAME,
            dimension=dims,
            metadata={"hnsw:space": "cosine"},
        )

    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Clear existing records (re-ingest)
    print("Clearing existing records...")
    try:
        collection.delete_records(ids=[])
    except Exception:
        pass

    # Generate embeddings
    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    # Build records
    print("Inserting records into Supabase...")
    records = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        record_id = f"{chunk.metadata['doc_id']}_{chunk.metadata['chunk_index']}"
        records.append({
            "id": record_id,
            "text": chunk.text,
            "embedding": embedding.tolist(),
            "metadata": chunk.metadata,
        })

    # Insert in batches of 100
    batch_size = 100
    total_batches = (len(records) + batch_size - 1) // batch_size
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        collection.upsert(batch)
        batch_num = i // batch_size + 1
        print(f"  Inserted batch {batch_num}/{total_batches}")

    # Get count
    count = collection.count()
    print(f"Successfully ingested {count} chunks into Supabase collection '{COLLECTION_NAME}'")

    # Print summary by module
    module_counts = {}
    for c in chunks:
        mod = c.metadata["module"]
        module_counts[mod] = module_counts.get(mod, 0) + 1

    print("Chunks per module:")
    for mod, cnt in sorted(module_counts.items()):
        print(f"  {mod}: {cnt} chunks")

    return 0


def main():
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print(f"Error: {docs_dir} does not exist")
        return 1

    print("Loading markdown files...")
    chunks = load_markdown_files(docs_dir)
    md_count = len(list(docs_dir.rglob("*.md")))
    print(f"Loaded {len(chunks)} chunks from {md_count} files")

    if not chunks:
        print("No content to ingest!")
        return 1

    return ingest_to_supabase(chunks)


if __name__ == "__main__":
    sys.exit(main())
