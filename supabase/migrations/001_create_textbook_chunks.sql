-- ============================================================
-- Supabase pgvector Migration for AI Textbook RAG
-- Run this in the Supabase SQL Editor:
--   https://app.supabase.com/project/<your-project>/sql
-- ============================================================

-- 1. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the textbook_chunks table
--    - id:        unique identifier per chunk (text)
--    - content:   the actual text chunk from the textbook
--    - embedding: 384-dimensional vector (all-MiniLM-L6-v2)
--    - metadata:  jsonb with module, title, section, doc_id, etc.
CREATE TABLE IF NOT EXISTS textbook_chunks (
    id          TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(384) NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 3. Create an HNSW index for fast cosine similarity search
--    Using cosine distance (matches ChromaDB default and the
--    hnsw:space = "cosine" config used by vecs).
CREATE INDEX IF NOT EXISTS textbook_chunks_embedding_idx
    ON textbook_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 4. Optional: add a GIN index on metadata for filtered queries
CREATE INDEX IF NOT EXISTS textbook_chunks_metadata_idx
    ON textbook_chunks
    USING gin (metadata);

-- 5. Verify the table was created
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'textbook_chunks'
ORDER BY ordinal_position;