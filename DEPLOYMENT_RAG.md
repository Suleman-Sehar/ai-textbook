# RAG Backend Deployment — Hugging Face Docker Space

The chatbot backend runs as a **Hugging Face Docker Space**.

> The frontend (this Docusaurus site) is still on Vercel at
> `https://physical-ai-textbook.vercel.app`.

## 1. Create the Space

1. Go to <https://huggingface.co/new-space>
2. Choose **Docker** as the SDK
3. Name it (e.g. `ai-textbook-backend`) and pick a Docker `null` license
4. Set the hardware to **CPU basic** (not ZeroGPU, which is Gradio-only)
5. Push this repo's backend files over the generated stub

> **Requires an HF PRO subscription.** Creating or running a Docker Space on
> free `cpu-basic` hardware fails with `HTTP 402`: *"hosting Gradio and Docker
> Spaces on free cpu-basic requires a PRO subscription."* Subscribe at
> <https://huggingface.co/pro>. The `Dockerfile` here is plain and portable, so
> any Docker host that binds `0.0.0.0:7860` runs it unchanged if you would
> rather not pay.

The Space reads its configuration from the YAML front matter at the top of
`README.md`:

```yaml
---
title: AI Textbook RAG API
sdk: docker
app_port: 7860
---
```

`short_description` must be 60 characters or fewer; the Hub rejects the push
otherwise.

## 2. Push the backend

```bash
huggingface-cli login          # or: hf auth login
git remote add space https://huggingface.co/spaces/<hf-username>/<space-name>
git push space main
```

Watch the build under **Settings -> Logs**, or locally:

```bash
watch curl -s https://Suleman-sehar-ai-textbook-backend.hf.space/health
```

The Space URL is `https://Suleman-sehar-ai-textbook-backend.hf.space`.

> Only the backend is pushed to the Space: `Dockerfile`, `README.md`,
> `requirements.txt`, `.dockerignore`, `scripts/` and `docs/`. The Docusaurus
> frontend stays in this repository and deploys to Vercel.

> The repository contains both the Docusaurus frontend and the FastAPI backend.
> `main` is the frontend's branch; the Space's own git history lives on the
> `space` remote, so pushing to `space` is safe and independent of `origin`.

## 3. Configure secrets

Add these under **Settings -> Variables and secrets** in the Space. Mark the
sensitive ones as secrets. `.env.example` documents every variable.

Only two are required:

| Name | Type | Value |
| --- | --- | --- |
| `GEMINI_API_KEY` | secret | From <https://aistudio.google.com/apikey> |
| `ALLOWED_ORIGINS` | variable | `https://physical-ai-textbook.vercel.app` |

That is enough: with no Supabase variables set the API builds its index
in-process from the committed `docs/` markdown, so there is no database to
provision and no ingest step.

### Optional: persistent Supabase index

Set `SUPABASE_DB_URL` to keep the index across restarts and skip the embedding
pass on cold start:

| Name | Type | Value |
| --- | --- | --- |
| `SUPABASE_DB_URL` | secret | Supabase → Project Settings → Database → Connection string (URI), session pooler |

```
postgresql://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

Then run `create extension if not exists vector;` once in the Supabase SQL
editor, and run `python scripts/ingest_rag.py` to populate the collection. If
Supabase is configured but unreachable, the API logs a warning and falls back
to the in-memory index rather than failing.

## 4. Verify

```bash
# 1. health - expect "ready": true, "backend": "memory", chunks ~361
curl https://Suleman-sehar-ai-textbook-backend.hf.space/health

# 2. a real grounded question
curl -X POST https://Suleman-sehar-ai-textbook-backend.hf.space/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the ROS 2 perception pipeline?"}'
```

The response should contain an `answer` drawn from the textbook plus a
`sources` array naming the module, title and section it came from.

Interactive API docs are at `/docs`.

## 5. Point the frontend at the Space

`docusaurus.config.js` already defaults `chatApiUrl` to this Space's URL. To
point it somewhere else, set one variable in the **Vercel** project settings and
redeploy:

```
VITE_CHAT_API_URL=https://<hf-username>-<space-name>.hf.space/api/chat
```

This is the only backend reference in the frontend. `docusaurus.config.js` reads
it at build time and exposes it to the browser through
`siteConfig.customFields.chatApiUrl`, because Docusaurus does not support
`import.meta.env` — a bug that previously made the chatbot fail in production
regardless of backend.

The widget handles Free Spaces sleeping: it shows a "server waking up" message,
times out after 90s, and retries once after 12s.

## Re-indexing

With the default in-memory backend there is nothing to re-index — the index is
built from `docs/` at every cold start. Push your `docs/` changes and redeploy.

For a Supabase-backed index, run the script locally after editing `docs/`:

```bash
python -m pip install -r requirements.txt
python scripts/ingest_rag.py
```

It prints the chunk count per module when finished. Chunk ids are
`<doc_id>_<chunk_index>`, so re-running is idempotent.

**Changing `EMBEDDING_MODEL` requires a full re-ingest.** `all-MiniLM-L6-v2`
produces 384-dim vectors, and vectors from different models are not comparable.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Space creation or hardware change returns HTTP 402 | Docker Spaces on free `cpu-basic` now require an HF PRO subscription | Subscribe at <https://huggingface.co/pro>, or run the same Dockerfile on another Docker host |
| Stage is `CONFIG_ERROR`, "ZeroGPU is only available on Gradio SDK" | The Space still requests ZeroGPU hardware, left over from when it was created as a Gradio Space | Edit the Space's hardware to `cpu-basic` in **Settings -> Hardware** (needs PRO for Docker Spaces) |
| Build fails at `pip install` | A pin in `requirements.txt` does not exist on PyPI | Check the build log for the package name |
| Space sleeps mid-conversation | Free Spaces sleep after inactivity | The widget already retries once; ask again to wake it |
| `/health` shows `"ready": false` | Read `last_error` in the same payload | Usually a bad `GEMINI_API_KEY` or a failed model download |
| `POST /api/chat` → `503 "Backend not ready"` | Initialisation failed | Check Space logs |
| `POST /api/chat` → `502 LLM error` | Gemini rejected the call | Check `GEMINI_API_KEY` and the quota for the project |
| Browser CORS error | Origin not allowed | Add it to `ALLOWED_ORIGINS`, comma separated, no trailing slash |
| Answers are empty or wrong | Stale index or wrong embedding model | Redeploy to rebuild, or re-run `scripts/ingest_rag.py` |
| `chunks_in_db: 0` | Index still building | Wait for `RAG ready` in the Space logs |
