#!/usr/bin/env python3
"""
RAG Backend API for Physical AI & Humanoid Robotics Textbook
Exposes POST /api/chat endpoint for the frontend chatbot widget.
Uses Google Gemini for LLM generation.
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
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

# Initialize components
logger.info("Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(COLLECTION_NAME, embedding_function=None)

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
    """Retrieve relevant chunks from ChromaDB."""
    query_embedding = embedding_model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        chunks.append({
            "text": doc,
            "metadata": meta,
            "distance": dist
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
    return {
        "status": "healthy",
        "chunks_in_db": collection.count(),
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