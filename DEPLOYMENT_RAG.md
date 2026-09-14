# RAG Backend Deployment Guide (Render + Supabase pgvector)

This guide covers deploying the Python FastAPI RAG backend to Render,
using Supabase (pgvector) for vector storage and Google Gemini for LLM generation.

---

## Prerequisites

1. **Get your Gemini API key:**
   - Go to https://aistudio.google.com/apikey
   - Create a new API key
   - Copy it for use below

2. **Set up Supabase:**
   - Go to https://supabase.com → New Project
   - Run the SQL migration in `supabase/migrations/001_create_textbook_chunks.sql`
   - Copy your Project URL and service_role key from Settings → API

3. **GitHub repo** with this codebase pushed

---

## Step 1: Run the Supabase SQL Migration

In the Supabase SQL Editor, run the contents of
[`supabase/migrations/001_create_textbook_chunks.sql`](./supabase/migrations/001_create_textbook_chunks.sql):

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS textbook_chunks (
    id          TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(384) NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS textbook_chunks_embedding_idx
    ON textbook_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## Step 2: Deploy to Render

### Option A: Render Blueprint (Recommended)

1. Go to https://dashboard.render.com
2. Click **Deploy New Web Service**
3. Connect your GitHub repo: `Suleman-Sehar/ai-textbook`
4. Render detects `render.yaml` automatically
5. Click **Apply**

### Option B: Manual Web Service

1. Go to https://dashboard.render.com → **New Web Service**
2. Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python scripts/rag_api.py`
5. Plan: **Starter** ($7/mo, always-on) or **Free** (spins down after 15min)

---

## Step 3: Set Environment Variables on Render

Go to **Settings → Environment Variables** and add:

| Key | Value | Source |
|-----|-------|--------|
| `SUPABASE_URL` | `https://wmiedukhvkickdzyxstl.supabase.co` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | `your-service-role-key` | Supabase → Settings → API → service_role key |
| `GEMINI_API_KEY` | `your-gemini-key` | Google AI Studio |
| `PORT` | `8000` | (default) |

---

## Step 4: Run Ingestion

After the service is live, run the ingestion script to populate the
`textbook_chunks` table with embeddings:

```bash
# Option A: Run locally (requires .env with SUPABASE_URL + SUPABASE_SERVICE_KEY)
python scripts/ingest_rag.py

# Option B: Run on Render (one-time command)
render run --service ai-textbook-rag --command "python scripts/ingest_rag.py"
```

This will embed all 361 textbook chunks and insert them into Supabase.

---

## Step 5: Update Vercel Frontend

1. Go to Vercel → **Settings → Environment Variables**
2. Set:
   ```
   VITE_CHAT_API_URL = https://your-render-service.onrender.com/api/chat
   ```
3. **Redeploy** the Vercel project

---

## Architecture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│  Vercel (Next)  │ ──────────────► │  Render          │
│  Frontend       │  /api/chat     │  Python FastAPI  │
│  (Static + SSR) │                 │  + Gemini LLM    │
└─────────────────┘                 └────────┬─────────┘
                                             │
                                    PostgreSQL + pgvector
                                    (Supabase Cloud)
```

---

## Environment Variables Summary

| Variable | Where Set | Purpose |
|----------|-----------|---------|
| `SUPABASE_URL` | Render | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Render | Supabase service_role key (secret) |
| `GEMINI_API_KEY` | Render | Google Gemini API key (secret) |
| `VITE_CHAT_API_URL` | Vercel | Frontend backend URL (public) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Collection does not exist" | Run the SQL migration in Supabase |
| "relation textbook_chunks does not exist" | Verify migration ran successfully |
| "Module not found: vecs" | Ensure `vecs==0.0.22` in requirements.txt |
| "vector(384) dimension mismatch" | Verify embedding model is all-MiniLM-L6-v2 |
| CORS errors | FastAPI allows all origins (`*`) |
| Gemini 429 rate limit | Free tier is 15 RPM; implement retry/backoff if needed |

---

## Security Notes

- Never commit `.env` to version control
- Use platform secret management for `SUPABASE_SERVICE_KEY` and `GEMINI_API_KEY`
- CORS is open (`*`) for development; restrict in production if needed:
  ```python
  # In rag_api.py, change:
  allow_origins=["https://your-vercel-domain.vercel.app"]
  ```