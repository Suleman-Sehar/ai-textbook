#!/usr/bin/env python3
"""
RAG Backend API for Physical AI & Humanoid Robotics Textbook
Exposes POST /api/chat endpoint for the frontend chatbot widget.
Uses Google Gemini for LLM generation and Supabase (pgvector) for vector storage.
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import vecs
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_textbook")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TOP_K = int(os.getenv("TOP_K", "5"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))

# System prompt for grounded responses
SYSTEM_PROMPT = """You are a knowledgeable assistant for the "Physical AI & Humanoid Robotics Textbook".
Your role is to answer questions based ONLY on the provided context from the textbook.

RULES:
1. Answer ONLY using the provided context. Do not use external knowledge.
2. If the context doesn't contain enough information to answer, say so clearly: "I don't have enough information in the textbook to answer this question."
3. Cite your sources by referencing the module, week, and section titles.
4. Be concise but thorough. Focus on educational value.
5. If asked about something not covered in the textbook, politely decline and suggest what IS covered.

The textbook covers 4 modules over 13 weeks:
- Module 1 (Weeks 1-5): ROS 2 Nervous System - Foundations, Sensing, Motor Control, Perception, Digital Twin
- Module 2 (Weeks 6-7): Digital Twin - Physics & Interaction, Human-Robot Interaction
- Module 3 (Weeks 8-10): NVIDIA Isaac AI Brain - Vision, Mapping, Navigation
- Module 4 (Weeks 11-13): Vision-Language-Action - Kinematics, Decision-Making, Full System Integration
"""


def _ensure_collection():
    """Get the Supabase pgvector collection, creating it if missing."""
    logger.info("Initializing Supabase pgvector...")
    vx = vecs.Client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    dims = 384  # all-MiniLM-L6-v2 produces 384-dim embeddings

    try:
        collection = vx.get_collection(COLLECTION_NAME)
        count = collection.count()
        logger.info(f"Found existing collection '{COLLECTION_NAME}' with {count} chunks")
        if count > 0:
            return collection, vx
        logger.warning("Collection exists but is empty - will re-ingest")
    except Exception:
        logger.info(f"Collection '{COLLECTION_NAME}' not found - creating...")
        collection = vx.create_collection(
            name=COLLECTION_NAME,
            dimension=dims,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Auto-ingesting textbook content into Supabase...")
        collection = _auto_ingest(vx, collection)
        return collection, vx

    # Empty collection - re-ingest
    collection = _auto_ingest(vx, collection)
    return collection, vx


def _auto_ingest(vx, collection):
    """Run the textbook ingestion pipeline against Supabase pgvector."""
    from pathlib import Path
    import yaml
    from langchain_text_splitters import MarkdownHeaderValueSplitter

    docs_dir = Path("docs")
    if not docs_dir.exists():
        raise RuntimeError(f"Docs directory '{docs_dir}' not found - cannot auto-ingest")

    # --- chunking ---
    headers_to_split_on = [
        ("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4"),
    ]
    splitter = MarkdownHeaderValueSplitter(headers_to_split_on=headers_to_split_on)

    chunks = []
    for md_file in docs_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2]
                except yaml.YAMLError:
                    pass

        rel_path = md_file.relative_to(docs_dir)
        module = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        doc_id = frontmatter.get("id", rel_path.stem)
        title = frontmatter.get("title", rel_path.stem)

        try:
            header_chunks = splitter.split_text(content)
        except Exception:
            header_chunks = [{"page_content": content, "metadata": {}}]

        for i, hc in enumerate(header_chunks):
            chunk_text = hc.page_content if hasattr(hc, "page_content") else str(hc)
            chunk_meta = hc.metadata if hasattr(hc, "metadata") else {}
            if not chunk_text.strip():
                continue

            metadata = {
                "source_file": str(rel_path),
                "module": module,
                "doc_id": doc_id,
                "title": title,
                "sidebar_label": frontmatter.get("sidebar_label", title),
                "section": chunk_meta.get("h1", "") or chunk_meta.get("h2", "") or chunk_meta.get("h3", "") or "Introduction",
                "subsection": chunk_meta.get("h2", "") or chunk_meta.get("h3", "") or chunk_meta.get("h4", "") or "",
                "chunk_index": i,
            }
            metadata.update(frontmatter)
            chunks.append({"text": chunk_text.strip(), "metadata": metadata})

    if not chunks:
        raise RuntimeError("No chunks produced from docs/ - cannot auto-ingest")

    # --- embeddings ---
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    # --- store ---
    logger.info("Storing in Supabase...")
    try:
        collection.delete_records(ids=[])
    except Exception:
        pass

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        record_id = f"{chunk['metadata']['doc_id']}_{chunk['metadata']['chunk_index']}"
        records.append({
            "id": record_id,
            "text": chunk["text"],
            "embedding": embedding.tolist(),
            "metadata": chunk["metadata"],
        })

    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        collection.upsert(batch)

    count = collection.count()
    logger.info(f"Auto-ingested {count} chunks into Supabase collection '{COLLECTION_NAME}'")
    return collection


# Initialize components
collection, vx = _ensure_collection()

logger.info("Loading embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

logger.info("Initializing Gemini client...")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set! LLM responses will not work.")
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# Pydantic models
class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class SourceCitation(BaseModel):
    module: str
    title: str
    section: str
    doc_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    confidence: float


def retrieve_context(question: str, top_k: int = TOP_K) -> List[dict]:
    """Retrieve relevant chunks from Supabase pgvector."""
    query_embedding = embedding_model.encode([question]).tolist()
    results = collection.query(
        query_embedding=query_embedding,
        n_results=top_k,
        include=["text", "metadata", "distance"],
    )

    chunks = []
    for record_id, dist, meta, text in zip(
        results.get("ids", [[]])[0] if isinstance(results.get("ids"), dict) else results.get("ids", []),
        results.get("distances", [[]])[0] if isinstance(results.get("distances"), dict) else results.get("distances", []),
        results.get("metadatas", [[]])[0] if isinstance(results.get("metadatas"), dict) else results.get("metadatas", []),
        results.get("documents", [[]])[0] if isinstance(results.get("documents"), dict) else results.get("documents", []),
    ):
        chunks.append({
            "text": text,
            "metadata": meta or {},
            "distance": dist if dist is not None else 0.0,
        })
    return chunks


def build_context(chunks: List[dict]) -> tuple[str, List[SourceCitation]]:
    """Build context string and source citations from retrieved chunks."""
    context_parts = []
    sources = []
    seen_sources = set()

    total_chars = 0
    for chunk in chunks:
        meta = chunk["metadata"]
        text = chunk["text"]

        # Create source citation
        source_key = (meta.get("doc_id"), meta.get("section"))
        if source_key not in seen_sources:
            sources.append(SourceCitation(
                module=meta.get("module", "unknown"),
                title=meta.get("title", "Unknown"),
                section=meta.get("section", "Unknown"),
                doc_id=meta.get("doc_id", "unknown")
            ))
            seen_sources.add(source_key)

        # Add to context with citation info
        citation = f"[Source: {meta.get('title', 'Unknown')} > {meta.get('section', 'Unknown')}]"
        context_part = f"{citation}\n{text}"

        if total_chars + len(context_part) > MAX_CONTEXT_CHARS:
            break

        context_parts.append(context_part)
        total_chars += len(context_part)

    return "\n\n---\n\n".join(context_parts), sources


def generate_answer(question: str, context: str) -> str:
    """Generate grounded answer using Google Gemini."""
    if not genai_client:
        return "Error: Gemini API key not configured. Please set GEMINI_API_KEY environment variable."

    try:
        prompt = f"Context from textbook:\n{context}\n\nQuestion: {question}"
        cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=500,
        )
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=cfg,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg or "rate" in error_msg.lower():
            return f"[LLM rate-limited - showing retrieved context]\n\nBased on the textbook, here are the relevant passages:\n\n{context[:2000]}..."
        return f"Error generating answer: {error_msg}"


# FastAPI app
app = FastAPI(title="AI Textbook RAG API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    try:
        chunk_count = collection.count()
    except Exception:
        chunk_count = "unknown"
    return {
        "status": "healthy",
        "chunks_in_db": chunk_count,
        "embedding_model": EMBEDDING_MODEL,
        "llm_configured": genai_client is not None,
        "llm_model": GEMINI_MODEL,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - RAG query + generation."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not genai_client:
        raise HTTPException(status_code=503, detail="LLM not configured. Set GEMINI_API_KEY.")

    try:
        # Retrieve relevant chunks
        top_k = request.top_k or TOP_K
        chunks = retrieve_context(request.question, top_k)

        if not chunks:
            return ChatResponse(
                answer="I couldn't find any relevant information in the textbook for your question.",
                sources=[],
                confidence=0.0
            )

        # Build context and get sources
        context, sources = build_context(chunks)

        # Calculate confidence based on retrieval distances
        avg_distance = sum(c["distance"] for c in chunks) / len(chunks)
        confidence = max(0.0, 1.0 - avg_distance)  # Lower distance = higher confidence

        # Generate answer
        answer = generate_answer(request.question, context)

        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=round(confidence, 3)
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting RAG API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)