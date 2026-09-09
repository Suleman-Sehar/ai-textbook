#!/usr/bin/env python3
"""
RAG Ingestion Script for Physical AI & Humanoid Robotics Textbook
Chunks content by headings, generates embeddings, stores in ChromaDB.
"""

import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter


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
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

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


def ingest_to_chromadb(chunks: List[ContentChunk], persist_dir: str = "./chroma_db", collection_name: str = "ai_textbook"):
    """Ingest chunks into ChromaDB with embeddings."""
    print(f"Initializing ChromaDB at {persist_dir}...")

    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))

    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass

    collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    print("Storing in ChromaDB...")
    ids = [f"{c.metadata['doc_id']}_{c.metadata['chunk_index']}" for c in chunks]
    metadatas = [c.metadata for c in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas
    )

    count = collection.count()
    print(f"Successfully ingested {count} chunks into collection '{collection_name}'")

    # Print summary by module
    module_counts = {}
    for c in chunks:
        mod = c.metadata["module"]
        module_counts[mod] = module_counts.get(mod, 0) + 1

    print("\nChunks per module:")
    for mod, cnt in sorted(module_counts.items()):
        print(f"  {mod}: {cnt} chunks")

    return collection


def main():
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print(f"Error: {docs_dir} does not exist")
        return 1

    print("Loading markdown files...")
    chunks = load_markdown_files(docs_dir)
    print(f"Loaded {len(chunks)} chunks from {len(list(docs_dir.rglob('*.md')))} files")

    if not chunks:
        print("No content to ingest!")
        return 1

    ingest_to_chromadb(chunks)
    return 0


if __name__ == "__main__":
    exit(main())