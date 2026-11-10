---
title: AI Textbook RAG API
emoji: 📚
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: RAG chatbot over the AI textbook
---

# AI Textbook RAG API

FastAPI backend powering the AI Textbook chatbot. Retrieval-augmented generation
over the textbook `docs/` directory, deployed as a Hugging Face Docker Space.

| Component | Choice |
| --- | --- |
| Embeddings | `sentence-transformers` / `all-MiniLM-L6-v2` (384-dim) |
| Vector store | In-process NumPy cosine index |
| LLM | Google Gemini (`gemini-3.6-flash`) |
| Runtime | Hugging Face Docker Space, `0.0.0.0:7860` |

## Why the vector store is in-process

The HF disk is **ephemeral**: anything written to `/app` is wiped on rebuild and
restart. A persisted local index would therefore be lost every time, so the
index is built once with `python scripts/build_index.py` and the committed
artefacts (`data/index.npy` + `data/index.json`) are loaded in milliseconds on
every cold start. The textbook is only 361 chunks (384-dim, ~0.5 MB), so this
needs no database, no credentials, and no ingest step.

## Endpoints

### `GET /health`

Always returns `200` so a sleeping or warming Space is not reported as dead.
Check the `ready` boolean rather than the HTTP status.

```json
{
  "status": "healthy",
  "ready": true,
  "chunks_in_db": 361,
  "backend": "precomputed",
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_model": "gemini-3.6-flash",
  "llm_configured": true,
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
| `EMBEDDING_MODEL` | no | `sentence-transformers/all-MiniLM-L6-v2` | Must match the model recorded in `data/index.json` |
| `GEMINI_MODEL` | no | `gemini-3.6-flash` | Gemini model id |
| `TOP_K` | no | `5` | Chunks retrieved per question |
| `MAX_CONTEXT_CHARS` | no | `8000` | Context budget sent to the LLM |
| `PORT` | no | `7860` | Listen port (HF requires 7860) |
| `LLM_TIMEOUT_MS` | no | `60000` | Gemini request timeout |
| `RETRIEVE_TIMEOUT_S` | no | `30` | Retrieval budget for one chat request |
| `WARMUP_ON_START` | no | `true` | Load models in the background after boot |
| `DOCS_DIR` | no | `docs` | Markdown source directory |
| `INDEX_DIR` | no | `./data` | Directory holding `index.npy` / `index.json` |
| `EMBED_BACKEND` | no | `fastembed` | `fastembed` (ONNX) or `sentence-transformers` (torch) |
| `LOG_LEVEL` | no | `INFO` | Uvicorn log level |

### CORS

`ALLOWED_ORIGINS` is a comma-separated list, for example:

```
ALLOWED_ORIGINS=https://physical-ai-textbook.vercel.app,https://your-org.github.io
```

`http://localhost:3000`, `http://127.0.0.1:3000` and `http://localhost:5173`
are always allowed for local development.

## Deployment

### Backend — Hugging Face Space

The backend is a Docker Space that binds `0.0.0.0:7860`:

1. Go to <https://huggingface.co/new-space> and create a Space with the **Docker** SDK.
2. Push this repository's backend files over the generated stub:
   ```bash
   huggingface-cli login
   git remote add space https://huggingface.co/spaces/<user>/<space>
   git push space main
   ```
3. Under **Settings -> Variables and secrets**, add:

   | Name | Type | Value |
   | --- | --- | --- |
   | `GEMINI_API_KEY` | secret | From <https://aistudio.google.com/apikey> |
   | `ALLOWED_ORIGINS` | variable | `https://physical-ai-textbook.vercel.app` |

   That is all that is required: with no database configured the API loads the
   committed `data/index.*` artefacts at startup.

The Space URL is `https://<user>-<space>.hf.space`. Free Spaces sleep when
idle; the frontend handles this with a "server waking up" state, a timeout, and
one retry.

### Frontend — Vercel

The Docusaurus site deploys to Vercel. It is the only consumer of the backend:

```
VITE_CHAT_API_URL=https://<user>-<space>.hf.space/api/chat
```

Set `VITE_CHAT_API_URL` in the Vercel project environment (or in `.env` for
local dev) and redeploy. `docusaurus.config.js` reads it at build time and
exposes it to the browser through `siteConfig.customFields.chatApiUrl`. When
nothing is set, the widget falls back to `http://localhost:7860/api/chat` for
local development.

### Re-indexing the textbook

The index is built once with:

```bash
python scripts/build_index.py
```

It chunks every markdown file under `docs/` by heading, embeds with
`EMBEDDING_MODEL`, and writes `data/index.npy` + `data/index.json`. Push the
updated artefacts and redeploy the Space. Changing `EMBEDDING_MODEL` requires a
full rebuild: vectors from two models are not comparable.

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
- **Backend**: FastAPI + Gemini (Hugging Face Docker Space)
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
cp .env.example .env      # fill in GEMINI_API_KEY and ALLOWED_ORIGINS
python scripts/build_index.py
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

The site deploys to Vercel by importing this repository; Vercel auto-detects the
Docusaurus preset (`npm run build`, output directory `build`). Add
`VITE_CHAT_API_URL` to the Vercel project environment variables and redeploy.

## 📖 Content Overview

This textbook provides a comprehensive introduction to Physical AI and Humanoid Robotics, connecting digital AI systems to physical embodiment. Each module builds on previous concepts, creating a cohesive learning experience from foundational concepts to advanced system integration.

## 🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
