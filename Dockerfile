# RAG API Dockerfile for Railway/Render/Fly.io
# Uses Python 3.11 slim for smaller image

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ChromaDB and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/rag_api.py .
COPY scripts/ingest_rag.py .

# Copy ChromaDB data (for initial deployment - will be persisted via volume)
COPY chroma_db/ ./chroma_db/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the API server
CMD ["python", "rag_api.py"]