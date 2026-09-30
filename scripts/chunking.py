#!/usr/bin/env python3
"""Markdown chunking for the AI Textbook RAG pipeline.

A dependency-free replacement for the previously pinned
``langchain_text_splitters.MarkdownHeaderValueSplitter``. Dropping the langchain
stack removes four heavy transitive dependencies from the container image while
keeping identical splitting semantics:

* split on ATX headers (``#`` .. ``####``)
* strip the header line from the emitted content
* accumulate the most recent header of each level into metadata
* drop whitespace-only sections

Frontmatter is parsed with PyYAML when available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:  # pragma: no cover - PyYAML is a hard requirement at runtime
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

HEADER_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")

#: Header level -> metadata key, matching the previous langchain configuration.
HEADER_KEYS: Dict[int, str] = {1: "h1", 2: "h2", 3: "h3", 4: "h4"}


@dataclass
class Chunk:
    """A chunk of textbook prose plus the metadata used for citation."""

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def record_id(self) -> str:
        """Stable identifier so re-ingestion is idempotent."""
        return f"{self.metadata['doc_id']}_{self.metadata['chunk_index']}"


def split_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Return ``(frontmatter, body)`` for a markdown document."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter: Dict[str, Any] = {}
    if yaml is not None:
        try:
            loaded = yaml.safe_load(parts[1])
            if isinstance(loaded, dict):
                frontmatter = loaded
        except yaml.YAMLError:
            frontmatter = {}
    return frontmatter, parts[2]


def split_headers(text: str) -> List[Tuple[str, Dict[str, str]]]:
    """Split markdown into ``(content, header_metadata)`` sections.

    Headers inside fenced code blocks are ignored.
    """
    sections: List[Tuple[str, Dict[str, str]]] = []
    headers: Dict[str, str] = {}
    buffer: List[str] = []
    in_fence = False
    current_levels = sorted(HEADER_KEYS.keys(), reverse=True)

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            sections.append((body, dict(headers)))
        buffer.clear()

    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue

        match = None if in_fence else HEADER_RE.match(line)
        if match and len(match.group(1)) in HEADER_KEYS:
            flush()
            level = len(match.group(1))
            # A new header at level N invalidates every deeper level.
            for deeper in current_levels:
                if deeper >= level:
                    headers.pop(HEADER_KEYS[deeper], None)
            headers[HEADER_KEYS[level]] = match.group(2).strip()
            continue

        buffer.append(line)

    flush()
    return sections


def chunk_markdown(content: str) -> List[Tuple[str, Dict[str, str]]]:
    """Frontmatter-stripped body -> header sections."""
    _, body = split_frontmatter(content)
    return split_headers(body)


def load_markdown_files(docs_dir: Path) -> List[Chunk]:
    """Chunk every markdown file under ``docs_dir`` with citation metadata."""
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        raise RuntimeError(f"Docs directory '{docs_dir}' not found - cannot ingest")

    chunks: List[Chunk] = []
    md_files = sorted(docs_dir.rglob("*.md"))
    if not md_files:
        raise RuntimeError(f"No markdown files found under '{docs_dir}' - cannot ingest")

    for md_file in md_files:
        raw = md_file.read_text(encoding="utf-8")
        frontmatter, _ = split_frontmatter(raw)

        rel_path = md_file.relative_to(docs_dir)
        module = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        doc_id = str(frontmatter.get("id", rel_path.stem))
        title = str(frontmatter.get("title", rel_path.stem))
        sidebar_label = str(frontmatter.get("sidebar_label", title))

        for index, (body, header_meta) in enumerate(chunk_markdown(raw)):
            metadata: Dict[str, Any] = {
                "source_file": str(rel_path),
                "module": module,
                "doc_id": doc_id,
                "title": title,
                "sidebar_label": sidebar_label,
                "section": (
                    header_meta.get("h1")
                    or header_meta.get("h2")
                    or header_meta.get("h3")
                    or "Introduction"
                ),
                "subsection": (
                    header_meta.get("h2")
                    or header_meta.get("h3")
                    or header_meta.get("h4")
                    or ""
                ),
                "chunk_index": index,
            }
            # Page frontmatter wins, matching the previous ingestion behaviour.
            metadata.update(frontmatter)
            chunks.append(Chunk(text=body, metadata=metadata))

    if not chunks:
        raise RuntimeError(f"No chunks produced from '{docs_dir}' - cannot ingest")

    return chunks


def record_id(chunk: Chunk) -> str:
    """Functional alias for :attr:`Chunk.record_id`."""
    return chunk.record_id


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
    produced = load_markdown_files(target)
    print(f"{len(produced)} chunks from {len(list(target.rglob('*.md')))} files")
    for chunk in produced[:3]:
        print(f"  [{chunk.metadata['module']}] {chunk.metadata['section']} "
              f"({len(chunk.text)} chars) id={record_id(chunk)}")
