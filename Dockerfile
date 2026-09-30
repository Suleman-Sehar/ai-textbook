# AI Textbook RAG API - Hugging Face Docker Space
# The Space serves the FastAPI app on 0.0.0.0:7860 (see README.md front matter).

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    EMBEDDING_MODEL=all-MiniLM-L6-v2

WORKDIR /app

# Build toolchain for wheels that need compiling (sentence-transformers, vecs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt lists/*

# CPU-only torch first: the default PyPI wheel bundles CUDA and is multiple GB.
RUN pip install --no-cache-dir \
        torch==2.9.1 \
        --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at build time so the Space starts warm.
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('${EMBEDDING_MODEL:-all-MiniLM-L6-v2}')" || \
    echo 'WARN: embedding model pre-download failed; it will download at runtime'

COPY scripts/rag_api.py scripts/ingest_rag.py scripts/chunking.py scripts/vector_store.py ./
COPY docs/ ./docs/

# HF Spaces require the service to run as uid 1000.
RUN useradd --create-home --uid 1000 user \
    && mkdir -p /home/user/.cache/huggingface \
    && chown -R user:user /app /home/user
USER user

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -fsS http://localhost:7860/health || exit 1

CMD ["python", "rag_api.py"]
