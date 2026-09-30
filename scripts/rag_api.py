#!/usr/bin/env python3
"""RAG Backend API for the Physical AI & Humanoid Robotics Textbook.

Retrieval-augmented generation over the textbook ``docs/`` directory:
  * embeddings  -> sentence-transformers ``all-MiniLM-L6-v2`` (384-dim)
  * vector store -> Supabase pgvector via ``vecs``
  * generation  -> Google Gemini

Deployed as a Hugging Face Docker Space on ``0.0.0.0:7860``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import anyio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from chunking import load_markdown_files
from vector_store import (
    DEFAULT_EMBEDDING_DIMENSION,
    SupabaseIndex,
    build_memory_index,
    clear_collection,
    get_collection,
    supabase_is_configured,
    upsert_chunks,
)

# `scripts/` is the working directory in the container, so a local .env wins.
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("rag_api")

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        logger.warning("Invalid integer for %s, using %d", name, default)
        return default


COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_textbook")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TOP_K = _int_env("TOP_K", 5)
MAX_CONTEXT_CHARS = _int_env("MAX_CONTEXT_CHARS", 8000)
# Generous by default: Free Spaces cold-start, and embedding a query on CPU
# torch can take a few seconds.
PORT = _int_env("PORT", 7860)
LLM_TIMEOUT_MS = _int_env("LLM_TIMEOUT_MS", 60_000)
RETRIEVE_TIMEOUT_S = _int_env("RETRIEVE_TIMEOUT_S", 30)
WARMUP_ON_START = os.getenv("WARMUP_ON_START", "true").lower() in {"1", "true", "yes"}
DOCS_DIR = Path(os.getenv("DOCS_DIR", "docs"))

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
]


def allowed_origins() -> List[str]:
    """CORS allow-list from ``ALLOWED_ORIGINS`` (comma separated)."""
    raw = os.getenv("ALLOWED_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]
    for origin in DEFAULT_ALLOWED_ORIGINS:
        if origin not in origins:
            origins.append(origin)
    return origins


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
- Module 4 (Weeks 11-13): Vision-Language-Action - Kinematics, Decision-Making, Full System Integration"""

NO_CONTEXT_ANSWER = (
    "I couldn't find any relevant information in the textbook for your question."
)

# --------------------------------------------------------------------------- #
# Lazily-initialised application state
# --------------------------------------------------------------------------- #

# Module-level import of Supabase/vecs/SentenceTransformer would make the whole
# app unimportable (and /health unreachable) whenever credentials or the network
# are unavailable - which is what takes a hosted backend down entirely.
# Initialise on first use behind a lock instead.

@dataclass
class State:
    index: Any = None
    embedding_model: Any = None
    genai_client: Any = None
    chunks: int = -1
    backend: str = ""
    last_error: str = ""
    ready: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


state = State()


def build_genai_client() -> Any:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )


def _ingest_to_supabase(model) -> None:
    """Chunk + embed ``docs/`` and upsert into the pgvector collection."""
    chunks = load_markdown_files(DOCS_DIR)
    logger.info("Chunked %d sections from %s", len(chunks), DOCS_DIR)

    embeddings = model.encode([c.text for c in chunks], batch_size=32, show_progress_bar=True)

    collection = get_collection(DEFAULT_EMBEDDING_DIMENSION)
    clear_collection(collection)
    written = upsert_chunks(collection, chunks, embeddings)

    state.index = SupabaseIndex(collection)
    state.chunks = len(state.index)
    logger.info("Ingested %d records into Supabase collection '%s'", written, COLLECTION_NAME)


def _build_index(model) -> None:
    """Select and initialise the vector index backend."""
    if supabase_is_configured():
        logger.info("Supabase detected - using pgvector via vecs")
        try:
            collection = get_collection(DEFAULT_EMBEDDING_DIMENSION)
            total = len(collection)
            if total <= 0:
                logger.warning("Collection '%s' is empty - ingesting", COLLECTION_NAME)
                _ingest_to_supabase(model)
            else:
                state.index = SupabaseIndex(collection)
                state.chunks = total
                logger.info("Supabase collection '%s' ready with %d chunks", COLLECTION_NAME, total)
            state.backend = "supabase"
            return
        except Exception as exc:
            # Never let a store outage take the whole chatbot down: the
            # textbook is committed, so an in-process index always works.
            logger.error(
                "Supabase unavailable (%s) - falling back to the in-memory index", exc
            )
            state.last_error = f"Supabase unavailable ({exc}); using in-memory index"

    logger.info("Building in-memory index from %s ...", DOCS_DIR)
    state.index = build_memory_index(model, DOCS_DIR)
    state.chunks = len(state.index)
    state.backend = "memory"


def ensure_ready() -> State:
    """Idempotently initialise the embedding model, index and LLM client."""
    if state.ready:
        return state

    with state.lock:
        if state.ready:
            return state

        logger.info("Initialising RAG state...")
        state.genai_client = build_genai_client()
        if state.genai_client is None:
            logger.warning("GEMINI_API_KEY not set - LLM answers will fail")

        state.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model ready (%s)", EMBEDDING_MODEL)

        _build_index(state.embedding_model)

        state.ready = True
        if not state.last_error:
            state.last_error = ""
        logger.info("RAG ready (backend=%s chunks=%d)", state.backend, state.chunks)
        return state


def reset_state() -> None:
    """Drop the cached state so the next request retries initialisation.

    ``last_error`` is deliberately preserved: callers set it immediately before
    calling this, and it is what ``/health`` reports.
    """
    with state.lock:
        state.ready = False
        state.index = None
        state.embedding_model = None
        state.genai_client = None


# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up in the background so a cold Space answers /health immediately
    # instead of blocking startup behind a model download.
    if WARMUP_ON_START:
        async def warm() -> None:
            try:
                await anyio.to_thread.run_sync(ensure_ready)
            except Exception as exc:  # pragma: no cover - logged, retried per request
                logger.error("Warmup failed: %s", exc)
                state.last_error = str(exc)
                reset_state()

        asyncio.create_task(warm())
    yield


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

app = FastAPI(title="AI Textbook RAG API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    # `allow_credentials=True` is invalid alongside a wildcard allow-list, and
    # the frontend sends no cookies, so keep it off.
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
async def root():
    return {
        "service": "AI Textbook RAG API",
        "docs": "/docs",
        "health": "/health",
        "chat": "POST /api/chat",
    }


@app.get("/health")
async def health_check():
    """Liveness + readiness. Always 200 so the Space is not killed while
    dependencies are still initialising; inspect the payload for readiness."""
    ready = state.ready
    chunks = state.chunks
    error = state.last_error

    if not ready:
        # Cheap, non-blocking probe so a restarted Space reports real status.
        try:
            await anyio.to_thread.run_sync(_probe_readiness)
            ready = state.ready
            chunks = state.chunks
            error = state.last_error
        except Exception as exc:
            error = str(exc)

    return {
        "status": "healthy" if ready else "starting",
        "ready": ready,
        "chunks_in_db": chunks,
        "backend": state.backend or None,
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": GEMINI_MODEL,
        "llm_configured": bool(os.getenv("GEMINI_API_KEY")),
        "collection": COLLECTION_NAME if state.backend == "supabase" else None,
        "last_error": error or None,
    }


def _probe_readiness() -> None:
    try:
        ensure_ready()
    except Exception as exc:
        logger.warning("Readiness probe failed: %s", exc)
        state.last_error = str(exc)
        reset_state()


# --------------------------------------------------------------------------- #
# RAG
# --------------------------------------------------------------------------- #

def retrieve_context(question: str, top_k: int) -> List[Dict[str, Any]]:
    query_embedding = state.embedding_model.encode([question])
    return state.index.search(query_embedding[0], top_k)


def build_context(chunks: List[Dict[str, Any]]) -> tuple[str, List[SourceCitation]]:
    parts: List[str] = []
    sources: List[SourceCitation] = []
    seen = set()
    used = 0

    for chunk in chunks:
        meta = chunk["metadata"]
        text = chunk["text"]
        if not text.strip():
            continue

        key = (meta.get("doc_id"), meta.get("section"))
        if key not in seen:
            seen.add(key)
            sources.append(SourceCitation(
                module=str(meta.get("module", "unknown")),
                title=str(meta.get("title", "Unknown")),
                section=str(meta.get("section", "Unknown")),
                doc_id=str(meta.get("doc_id", "unknown")),
            ))

        citation = f"[Source: {meta.get('title', 'Unknown')} > {meta.get('section', 'Unknown')}]"
        piece = f"{citation}\n{text}"
        if used + len(piece) > MAX_CONTEXT_CHARS:
            break

        parts.append(piece)
        used += len(piece)

    return "\n\n---\n\n".join(parts), sources


def generate_answer(question: str, context: str) -> str:
    if state.genai_client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    prompt = f"Context from textbook:\n{context}\n\nQuestion: {question}"
    response = state.genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=800,
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("LLM returned an empty response")
    return text


def run_chat(question: str, top_k: int) -> ChatResponse:
    chunks = retrieve_context(question, top_k)
    if not chunks:
        return ChatResponse(answer=NO_CONTEXT_ANSWER, sources=[], confidence=0.0)

    context, sources = build_context(chunks)
    if not context:
        return ChatResponse(answer=NO_CONTEXT_ANSWER, sources=[], confidence=0.0)

    avg_distance = sum(c["distance"] for c in chunks) / len(chunks)
    # cosine distance in [0, 2]; rescale into [0, 1]
    confidence = max(0.0, min(1.0, 1.0 - avg_distance))

    try:
        answer = generate_answer(question, context)
    except Exception as exc:
        message = str(exc)
        logger.error("LLM generation failed: %s", message)
        lowered = message.lower()
        if any(token in lowered for token in ("quota", "429", "rate limit", "resource_exhausted")):
            answer = (
                "The assistant is temporarily rate-limited. Here are the relevant "
                f"textbook passages:\n\n{context[:2000]}"
            )
        else:
            raise HTTPException(status_code=502, detail=f"LLM error: {message}")

    return ChatResponse(answer=answer, sources=sources, confidence=round(confidence, 3))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="LLM not configured. Set GEMINI_API_KEY.")

    top_k = request.top_k or TOP_K
    started = time.monotonic()

    try:
        await anyio.to_thread.run_sync(ensure_ready)
    except Exception as exc:
        logger.error("Initialisation failed: %s", exc)
        state.last_error = str(exc)
        reset_state()
        raise HTTPException(status_code=503, detail=f"Backend not ready: {exc}")

    try:
        with anyio.fail_after(RETRIEVE_TIMEOUT_S):
            result = await anyio.to_thread.run_sync(run_chat, question, top_k)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Retrieval timed out")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

    logger.info(
        "answered in %.2fs top_k=%d sources=%d", time.monotonic() - started, top_k, len(result.sources)
    )
    return result


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting RAG API on 0.0.0.0:%d", PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT, timeout_keep_alive=75)
