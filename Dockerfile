# AI Textbook RAG API - Docker image for Render (free tier) and HF Spaces.
#
# Sized for Render free: 512 MB RAM. torch is never installed; embeddings use
# fastembed (ONNX Runtime) at ~239 MB peak RSS.
#
# The app binds $PORT, which Render injects at runtime.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/home/user/.cache/huggingface \
    OMP_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    PORT=7860 \
    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

WORKDIR /app

# build-essential is only needed for the rare source-only wheel; onnxruntime and
# psycopg2-binary both ship manylinux wheels, so this layer usually stays empty.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/rag_api.py scripts/ingest_rag.py scripts/build_index.py \
     scripts/chunking.py scripts/vector_store.py scripts/embedder.py ./

# Textbook markdown (needed only for a from-scratch index rebuild) and the
# precomputed embeddings the API loads at startup.
COPY docs/ ./docs/
COPY data/ ./data/

# Pre-warm the embedding model into the image so a cold container starts fast.
RUN mkdir -p /home/user/.cache/huggingface \
    && python -c "import sys; sys.path.insert(0,'/app'); from embedder import get_embedder; get_embedder().load()" \
    || echo 'WARN: model pre-download failed; it will download at runtime'

# Render runs as a non-root user too.
RUN useradd --create-home --uid 1000 user \
    && chown -R user:user /app /home/user
USER user

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["python", "rag_api.py"]