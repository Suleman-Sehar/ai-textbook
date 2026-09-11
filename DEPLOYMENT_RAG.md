# RAG Backend Deployment Guide (Option B: Separate Always-On Service)

This guide covers deploying the Python FastAPI + ChromaDB RAG backend to Railway, Render, or Fly.io.
Uses Google Gemini 3.6-flash for LLM generation.

---

## Prerequisites

1. **Get your Gemini API key:**
   - Go to https://aistudio.google.com/apikey
   - Create a new API key
   - Copy it for use below

2. **GitHub repo** with this codebase pushed

---

## Option 1: Railway (Recommended - Easiest)

### Quick Deploy (2 minutes)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repo
4. Railway auto-detects `Dockerfile` and `railway.json`
5. Add environment variable:
   - `GEMINI_API_KEY` = your Gemini API key
   - `PORT` = `8000`
6. Click "Deploy"

### Persistent Storage
- Railway automatically provides persistent disk for `/app/chroma_db`
- Your existing `chroma_db/` data will be copied on first deploy
- On subsequent deploys, the volume persists

### Custom Domain (Optional)
- Settings → Domains → Generate Domain or add custom

---

## Option 2: Render (Free Tier Available)

### Quick Deploy

1. Go to https://dashboard.render.com/new/web-service
2. Connect GitHub repo
3. Render detects `render.yaml` (Blueprint)
4. Click "Apply" → Creates service with:
   - Free tier (spins down after 15min inactivity)
   - 1GB persistent disk for ChromaDB
   - Auto health checks
5. Add secret: `GEMINI_API_KEY` in Environment tab

### Note on Free Tier
- Service spins down after 15min of no requests
- First request after spin-down takes ~30-60s to wake up
- For production, upgrade to Starter ($7/mo) for always-on

---

## Option 3: Fly.io (Best Free Allowance)

### Quick Deploy

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch (creates app, provisions volume)
fly launch --copy-config --name ai-textbook-rag

# Set secret
fly secrets set GEMINI_API_KEY=your-gemini-key

# Deploy
fly deploy
```

### Free Allowance
- Up to 3 shared-cpu-1x VMs (256MB-512MB each) free forever
- 1GB persistent volume free
- No spin-down (always on)

---

## After Backend Deployment

### 1. Get Your Backend URL
- Railway: `https://your-app.up.railway.app`
- Render: `https://your-app.onrender.com`
- Fly.io: `https://ai-textbook-rag.fly.dev`

### 2. Update Vercel Environment Variables
Go to Vercel Dashboard → Project → Settings → Environment Variables:

```
VITE_CHAT_API_URL = https://your-backend-url/api/chat
```

### 3. Redeploy Vercel Frontend
- Vercel auto-redeploys on env var change, or trigger manually

### 4. Test the Chatbot
- Visit your Vercel URL
- Click the robot widget
- Ask: "What is Physical AI?"

---

## Updating Textbook Content (Re-indexing)

When you update `docs/` content:

```bash
# 1. Run ingestion locally
python scripts/ingest_rag.py

# 2. Commit and push chroma_db/ changes (if using git for data)
# OR: Re-deploy backend to pick up new data
# Railway/Render: git push triggers redeploy
# Fly.io: fly deploy
```

**Note:** For production, consider running ingestion as a CI step or separate job rather than committing the DB.

---

## Architecture Summary

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│  Vercel (Next)  │ ──────────────► │  Railway/Render  │
│  Frontend       │  /api/chat     │  Python FastAPI  │
│  (Static + SSR) │                 │  + ChromaDB      │
└─────────────────┘                 └──────────────────┘
       │                                      │
       │                              Persistent Disk
       │                              (chroma_db/)
       ▼                                      ▼
  CDN + Edge                          Python 3.11
  Global                              sentence-transformers
                                      Google Gemini 3.6-flash
```

---

## Cost Estimate (Monthly)

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Railway | $5 credit/mo | ~$5-10/mo |
| Render | Free (spins down) | $7/mo (Starter) |
| Fly.io | 3 VMs + 1GB vol free | ~$5/mo |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found: chromadb" | Ensure `requirements.txt` has all deps |
| ChromaDB permission errors | Dockerfile uses non-root user (UID 1000) |
| First request timeout | Increase healthcheck timeout, or upgrade from free tier |
| Embeddings slow on first request | Model downloads on first run (~90MB); subsequent fast |
| CORS errors | FastAPI already allows all origins (`*`) |
| Gemini 429 rate limit | Free tier is 15 RPM; implement retry/backoff if needed |

---

## Security Notes

- Never commit `.env` or `chroma_db/` to git
- Use platform secret management for `GEMINI_API_KEY`
- CORS is open (`*`) for development; restrict in production if needed:
  ```python
  # In rag_api.py, change:
  allow_origins=["https://your-vercel-domain.vercel.app"]
  ```