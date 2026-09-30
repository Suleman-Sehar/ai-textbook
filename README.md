---
title: AI Textbook RAG API
emoji: 📚
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Retrieval-augmented Q&A over the Physical AI & Humanoid Robotics textbook
---

# AI Textbook RAG API

FastAPI backend powering the AI Textbook chatbot. Retrieval-augmented generation
over the textbook `docs/` directory, deployed as a Hugging Face Docker Space.

| Component | Choice |
| --- | --- |
| Embeddings | `sentence-transformers` / `all-MiniLM-L6-v2` (384-dim) |
| Vector store | In-process NumPy cosine index (default), or Supabase pgvector |
| LLM | Google Gemini (`gemini-3.6-flash`) |
| Runtime | Hugging Face Docker Space, `0.0.0.0:7860` |

## Why the vector store is in-process by default

The HF disk is **ephemeral**: anything written to `/app` is wiped on rebuild and
restart. A persisted local index would therefore be lost every time, so the
default backend builds the index in memory from the committed `docs/` markdown
on every cold start. The textbook is only 361 chunks (384-dim, ~0.5 MB), so
this costs roughly 30 seconds of CPU once per cold start and then needs nothing
else — no database to provision, no credentials, no ingest step.

Set `SUPABASE_DB_URL` (or `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`) to switch to
a Supabase pgvector index instead. That keeps the index across restarts and
skips the embedding pass on cold start, at the cost of an external service. If
it is configured but unreachable, the API logs a warning and falls back to the
in-memory index rather than failing.

## Endpoints

### `GET /health`

Always returns `200` so a sleeping or warming Space is not reported as dead.
Check the `ready` boolean rather than the HTTP status.

```json
{
  "status": "healthy",
  "ready": true,
  "chunks_in_db": 361,
  "backend": "memory",
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_model": "gemini-3.6-flash",
  "llm_configured": true,
  "collection": null,
  "last_error": null
}
```

### `POST /api/chat`

```bash
curl -X POST https://<user>-<space>.hf.space/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the ROS 2 perception pipeline?"}'
```

```json
{
  "answer": "...",
  "sources": [
    {"module": "module-1-ros2", "title": "Week 4: Perception", "section": "...", "doc_id": "..."}
  ],
  "confidence": 0.63
}
```

## Environment variables

Set these under **Settings -> Variables and secrets** in the Space, marking the
sensitive ones as secrets. `.env.example` lists every one.

Only two are required to run: `GEMINI_API_KEY` and `ALLOWED_ORIGINS`.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | yes | - | Google AI Studio key used for generation |
| `ALLOWED_ORIGINS` | yes | - | Comma-separated frontend origins allowed by CORS |
| `SUPABASE_DB_URL` | no | - | Postgres DSN used by `vecs`; enables the persistent pgvector index |
| `SUPABASE_URL` | no | - | Supabase project URL, used to build the DSN |
| `SUPABASE_SERVICE_KEY` | yes* | - | Supabase service role key |
| `SUPABASE_REGION` | no | direct conn | Supabase region (`us-east-1`, `eu-central-1`, ...) for the pooler host |
| `ALLOWED_ORIGINS` | yes | - | Comma-separated frontend origins allowed by CORS |
| `COLLECTION_NAME` | no | `ai_textbook` | pgvector collection/table name |
| `EMBEDDING_MODEL` | no | `all-MiniLM-L6-v2` | Must match the model used at ingestion |
| `GEMINI_MODEL` | no | `gemini-3.6-flash` | Gemini model id |
| `TOP_K` | no | `5` | Chunks retrieved per question |
| `MAX_CONTEXT_CHARS` | no | `8000` | Context budget sent to the LLM |
| `PORT` | no | `7860` | Listen port (HF requires 7860) |
| `LLM_TIMEOUT_MS` | no | `60000` | Gemini request timeout |
| `RETRIEVE_TIMEOUT_S` | no | `30` | Retrieval budget for one chat request |
| `WARMUP_ON_START` | no | `true` | Load models in the background after boot |
| `DOCS_DIR` | no | `docs` | Markdown source directory |
| `LOG_LEVEL` | no | `INFO` | Uvicorn log level |

\* Either `SUPABASE_DB_URL`, or all three of `SUPABASE_URL` +
`SUPABASE_SERVICE_KEY` + `SUPABASE_REGION`.

### CORS

`ALLOWED_ORIGINS` is a comma-separated list, for example:

```
ALLOWED_ORIGINS=https://physical-ai-textbook.vercel.app,https://your-org.github.io
```

`http://localhost:3000`, `http://127.0.0.1:3000` and `http://localhost:5173`
are always allowed for local development.

## Deploying the backend

```bash
huggingface-cli login
git remote add space https://huggingface.co/spaces/<user>/<space>
git push space main
```

Add the secrets in the Space settings, then watch the build log. The Space URL
is `https://<user>-<space>.hf.space`.

Free Spaces sleep when idle. The frontend handles this with a "server waking up"
state, a timeout, and one retry.

## Re-indexing the textbook

With the default in-memory backend there is nothing to re-index: the index is
built from `docs/` at every cold start, so push your `docs/` changes and
redeploy. To refresh a Supabase-backed index without waiting for a Space
rebuild, run the ingestion script locally:

```bash
python -m pip install -r requirements.txt
cp .env.example .env     # fill in SUPABASE_DB_URL and GEMINI_API_KEY
python scripts/ingest_rag.py
```

It chunks every markdown file under `docs/` by heading, embeds with
`EMBEDDING_MODEL`, and upserts into `COLLECTION_NAME` using stable
`<doc_id>_<chunk_index>` ids, so re-running is idempotent. Changing
`EMBEDDING_MODEL` requires a full re-ingest: vectors from two models are not
comparable inside the same collection.

## Connecting the frontend

The chatbot widget reads a single variable:

```
VITE_CHAT_API_URL=https://<user>-<space>.hf.space/api/chat
```

Set it in the Vercel project environment for production, or in `.env` locally.
It is the only backend reference in the frontend.

---

# Physical AI & Humanoid Robotics Textbook

A comprehensive 19,752-word Docusaurus textbook covering Physical AI & Humanoid Robotics, structured in 4 modules over 13 weeks. This textbook provides a complete educational resource for understanding the intersection of artificial intelligence and physical robotics systems.

## 📚 Modules

### Module 1: ROS 2 Nervous System (Weeks 1-5)
- Week 1: Foundations of Physical AI
- Week 2: Sensing the World
- Week 3: Motor Control & Action
- Week 4: Perception Pipeline
- Week 5: Digital Twin Concepts

### Module 2: Digital Twin (Weeks 6-7)
- Week 6: Physics & Interaction Basics
- Week 7: Human-Robot Interaction Basics

### Module 3: NVIDIA Isaac AI Brain (Weeks 8-10)
- Week 8: Vision Systems
- Week 9: Mapping & Understanding Environments
- Week 10: Navigation & Path Planning

### Module 4: Vision-Language-Action (Weeks 11-13)
- Week 11: Kinematics & Movement
- Week 12: Decision-Making for Robots
- Week 13: Full System Overview

## 🚀 Features

- **19,752 words** of comprehensive content (within target 15,000-20,000 range)
- **4 complete modules** with structured learning progression
- **20+ conceptual examples** across all modules
- **12 diagrams** illustrating key concepts
- **Mobile-responsive** Docusaurus v3 interface
- **Modular navigation** with clear learning paths
- **Grounded chatbot** answering only from textbook content, with citations

## 🛠️ Tech Stack

- **Frontend**: Docusaurus v3
- **Language**: Markdown/MDX with React components
- **Backend**: FastAPI + Supabase pgvector + Gemini (Hugging Face Docker Space)
- **Frontend deployment**: Vercel
- **Build system**: Node.js 18+

## 📋 Requirements

- Node.js >= 18.0
- npm package manager
- Python >= 3.11 and pip (only needed to run the backend locally or re-index)
- Git for version control

## 🔧 Local Development

1. Clone the repository
2. Install frontend dependencies: `npm install`
3. Start the development server: `npm start`
4. Visit `http://localhost:3000` to view the textbook

To run the chatbot locally as well:

```bash
python -m pip install -r requirements.txt
cp .env.example .env      # fill in the values
python scripts/ingest_rag.py
python scripts/rag_api.py # serves on http://localhost:7860
```

The widget falls back to `http://localhost:7860/api/chat` on `localhost`; set
`VITE_CHAT_API_URL` to override it.

## 🏗️ Building for Production

```bash
npm run build
```

The built site will be available in the `build/` directory.

## 📊 Validation Scripts

- `scripts/check-wordcount.py` - Verify word count requirements
- `scripts/link-check.sh` - Check internal and external links
- `scripts/verify.sh` - Run all validation checks

## 🚀 Frontend Deployment

This project is configured for deployment to Vercel. The `vercel.json` file contains the necessary configuration for automatic builds and deployment. Add `VITE_CHAT_API_URL` to the Vercel project environment variables.

## 📖 Content Overview

This textbook provides a comprehensive introduction to Physical AI and Humanoid Robotics, connecting digital AI systems to physical embodiment. Each module builds on previous concepts, creating a cohesive learning experience from foundational concepts to advanced system integration.

## 🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
