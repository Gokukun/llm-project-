---
title: Rana Meet AI Assistant
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Self RAG Chat Bot

A hybrid-retrieval RAG (Retrieval-Augmented Generation) chatbot for Rana Meet's
portfolio.

It has three moving parts:

- **FastAPI backend** (`app/`) — scrapes web pages, splits them into chunks,
  embeds them locally with `sentence-transformers/all-MiniLM-L6-v2`, stores the
  vectors in **PostgreSQL + pgvector**, and builds a **BM25** index for keyword
  search.
- **Groq / GPT-OSS 120B** — answers questions using only the retrieved context.
- **Gradio UI** (`ui.py`) — a chat interface that calls the backend.

## Project structure

```
app/
  main.py          FastAPI app with /init and /ask endpoints
  ingest.py        Splits scraped page text into chunks
  scraping.py      Downloads and cleans web page text
  vectorestore.py  Stores embeddings and runs BM25 + vector hybrid search
  chat.py          Retrieves hybrid context and asks Groq's GPT-OSS model
ui.py              Gradio chat UI
data/              Optional source PDF (not used by the current API)
```

## How retrieval works

Each question uses hybrid retrieval:

1. **BM25** ranks chunks by keyword overlap using `rank_bm25`.
2. **Vector search** ranks chunks by cosine similarity in pgvector.
3. **Reciprocal Rank Fusion (RRF)** merges both rankings, and the top chunks
   are sent to `openai/gpt-oss-120b`.

You can also call the retrieval modes directly:

```python
from app.vectorestore import search

search("What projects has Rana worked on?", mode="hybrid")  # default
search("What projects has Rana worked on?", mode="vector")
search("What projects has Rana worked on?", mode="bm25")
```

## Prerequisites

- Python **3.10+**
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- PostgreSQL with the **pgvector** extension (local PostgreSQL, Supabase, Neon, ...)
- A **Groq API key** — create one at https://console.groq.com/keys

## Quick start

```bash
# 1. Install dependencies
uv sync

# 2. Create .env with GROQ_API_KEY, DATABASE_URL and INGEST_API_KEY

# 3. Start the API (terminal 1)
uv run uvicorn app.main:app --reload

# 4. Load documents (terminal 2)
curl -X POST http://127.0.0.1:8000/init \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Key: <your-ingest-key>" \
  -d '["https://gokukun.github.io/ranameet.github.io/"]'

# 5. Start the UI (terminal 3)
uv run python ui.py
```

Open the UI at **http://127.0.0.1:7860** and the API docs at
**http://127.0.0.1:8000/docs**.

---

## Step-by-step setup

### 1. Install dependencies

Using `uv` (recommended, reads `pyproject.toml` / `uv.lock`):

```bash
uv sync
```

Using `pip` instead:

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt -r requirements-ui.txt
```

> Run every command below from the project root (the folder containing
> `app/`, `ui.py`, and `pyproject.toml`).

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY="gsk_..."
DATABASE_URL="postgresql://user:password@localhost:5432/chatbot"
INGEST_API_KEY="pick-a-long-random-string"
```

| Variable         | Required | Description                                                        |
| ---------------- | -------- | ------------------------------------------------------------------ |
| `GROQ_API_KEY`   | Yes      | Groq API key used by the GPT-OSS model.                            |
| `DATABASE_URL`   | Yes      | PostgreSQL connection string.                                      |
| `INGEST_API_KEY` | Recommended | Shared secret required by `POST /init` in the `X-Ingest-Key` header. If unset, `/init` is unprotected. |
| `BACKEND_URL`    | No (UI)  | Full `/ask` URL the UI calls. Defaults to `http://127.0.0.1:8000/ask`. |

`.env` is already listed in `.gitignore` — never commit real keys.

### 3. Prepare the database

The API runs `CREATE EXTENSION IF NOT EXISTS vector` itself, so the database
user must be allowed to create the extension.

#### Option A: Docker (recommended on Windows)

This is the quickest way to get PostgreSQL with pgvector. Docker Desktop must
be running.

```bash
docker run -d --name chatbot-pg --restart unless-stopped \
  -e POSTGRES_PASSWORD=chatbotpass \
  -e POSTGRES_DB=meet \
  -p 5433:5432 \
  pgvector/pgvector:pg17
```

Then use this in `.env`:

```env
DATABASE_URL="postgresql://postgres:chatbotpass@localhost:5433/meet"
```

Port `5433` is used so the container does not conflict with a local PostgreSQL
installation on `5432`. The container starts automatically when Docker Desktop
starts, and its data is kept in the container's volume.

#### Option B: Local PostgreSQL

```bash
createdb chatbot
psql chatbot -c "CREATE EXTENSION IF NOT EXISTS vector"
```

If you use Supabase, Neon, or another hosted provider, create the database in
their dashboard and copy its connection string into `DATABASE_URL`. Append
`?sslmode=require` if the provider requires SSL.

**Special characters in the password must be URL-encoded.** For example, `@`
becomes `%40`:

```env
DATABASE_URL="postgresql://postgres:MyPass%40123@localhost:5432/chatbot"
```

### 4. Start the API

```bash
uv run uvicorn app.main:app --reload
```

If you installed with `pip` and activated the virtual environment:

```bash
uvicorn app.main:app --reload
```

Check that it is running:

- Health check: http://127.0.0.1:8000/health
- Interactive docs: http://127.0.0.1:8000/docs

### 5. Load documents

`POST /init` **drops and recreates** the `intellentx_docs` table, then scrapes,
chunks, embeds, and stores the given URLs. Run it again whenever you want to
reload the knowledge base. The current API ingests web pages only. Any local
PDFs in `data/` are reference material; they are not committed and are not
loaded by `/init`.

Replace `<your-ingest-key>` with the `INGEST_API_KEY` value from `.env` (or
omit the header if you left `INGEST_API_KEY` unset).

Bash / macOS / Linux:

```bash
curl -X POST http://127.0.0.1:8000/init \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Key: <your-ingest-key>" \
  -d '["https://gokukun.github.io/ranameet.github.io/"]'
```

Windows PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/init `
  -Headers @{ "X-Ingest-Key" = "<your-ingest-key>" } `
  -ContentType "application/json" `
  -Body '["https://gokukun.github.io/ranameet.github.io/"]'
```

The first ingest downloads the embedding model, so it can take a few minutes.
A successful response looks like:

```json
{ "status": "ok", "ingested": 42 }
```

### 6. Ask a question from the API

```bash
curl "http://127.0.0.1:8000/ask?q=What+projects+has+Rana+worked+on%3F"
```

### 7. Start the UI

```bash
uv run python ui.py
```

With `pip`, use `python ui.py` inside the activated virtual environment.

Open http://127.0.0.1:7860. The UI reads `BACKEND_URL`; if the API runs
elsewhere, set it before starting the UI:

```bash
# Bash
BACKEND_URL="http://127.0.0.1:8000/ask" uv run python ui.py

# PowerShell
$env:BACKEND_URL = "http://127.0.0.1:8000/ask"; uv run python ui.py
```

To change the Gradio port, set `PORT` (default `7860`). By default the UI binds
to `127.0.0.1`, so open **http://127.0.0.1:7860** (not `0.0.0.0`). To expose it
on your LAN, set `GRADIO_SERVER_NAME=0.0.0.0` and use your machine's LAN IP.

## API reference

| Method | Path    | Description                                                        |
| ------ | ------- | ------------------------------------------------------------------ |
| `GET`  | `/health` | Health check, returns `{"message": "server is running"}`.         |
| `POST` | `/init` | Rebuild the document/vector table from a JSON list of URLs; the BM25 index refreshes on the next query. Requires `X-Ingest-Key` when `INGEST_API_KEY` is set. |
| `GET`  | `/ask`  | Answer `?q=<question>` using hybrid BM25 + vector RAG. Returns `{"query": ..., "answer": ...}`. |

## Deploy on Hugging Face Spaces (recommended)

This project includes a `Dockerfile` and `deploy_app.py` that serve the Gradio
UI and FastAPI API from **one public URL**.

### 1. Create the database (Neon)

1. Create a free project at https://console.neon.tech.
2. Copy the **direct connection** string (not the pooled one).
3. Keep `?sslmode=require` in the URL.

```env
DATABASE_URL="postgresql://user:password@ep-....neon.tech/neondb?sslmode=require"
```

`/init` creates the `vector` extension, table, and HNSW index. If your Neon user
cannot create extensions, run `CREATE EXTENSION IF NOT EXISTS vector;` once in
the Neon SQL editor.

### 2. Create the Space

1. Open https://huggingface.co/new-space.
2. Name it, for example, `rana-meet-ai`.
3. Choose **Docker** as the SDK and **CPU basic (free)** hardware.
4. Set visibility to **Public**.

### 3. Add secrets

In the Space, open **Settings → Variables and secrets** and add:

| Name | Value |
| --- | --- |
| `GROQ_API_KEY` | Your Groq API key |
| `DATABASE_URL` | Your Neon connection string |
| `INGEST_API_KEY` | A long random secret |

Do not add `BACKEND_URL`; the combined app calls the RAG pipeline directly.

### 4. Push the code

Commit your local changes first:

```bash
git add .
git commit -m "Add hybrid RAG and deployment setup"
git push origin main
```

Then push to the Space:

```bash
git remote add hf https://huggingface.co/spaces/<username>/rana-meet-ai
git push hf main --force
```

Use your Hugging Face username and an access token with write permission as the
password. Create a token at https://huggingface.co/settings/tokens. The `--force`
is only needed because a newly created Space starts with its own README.

The Space builds the image, pre-downloads the embedding model, and starts the
combined app on port `7860`.

### 5. Load the knowledge base

After the Space status is **Running**:

```bash
curl -X POST https://<username>-rana-meet-ai.hf.space/init \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Key: <your-ingest-key>" \
  -d '["https://gokukun.github.io/ranameet.github.io/"]'
```

PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri https://<username>-rana-meet-ai.hf.space/init `
  -Headers @{ "X-Ingest-Key" = "<your-ingest-key>" } `
  -ContentType "application/json" `
  -Body '["https://gokukun.github.io/ranameet.github.io/"]'
```

A successful response looks like `{"status":"ok","ingested":8}`.

### 6. Use it on your resume

Use the direct Space URL:

```
https://<username>-rana-meet-ai.hf.space
```

For example: `https://gokukun-rana-meet-ai.hf.space`.

Free Spaces sleep after inactivity, so the first visit can take 30–60 seconds.
To keep it warm, create a free uptime monitor (for example UptimeRobot) that
requests `/health` every 5 minutes.

### Test the combined app locally

```bash
uv run uvicorn deploy_app:app --host 127.0.0.1 --port 7861
```

Open http://127.0.0.1:7861. The API docs are at `/docs` and the health check is
`/health`.

## Deploy on Render (alternative)

The same `Dockerfile` works as a single Render Web Service:

1. Create a **Web Service** from this repository and choose **Docker**.
2. Add `GROQ_API_KEY`, `DATABASE_URL`, and `INGEST_API_KEY`.
3. Use `/health` as the health check path.
4. Choose at least 2 GB RAM; the free 512 MB instance may not fit PyTorch.

Render sets `PORT`, and the container serves the UI and API from one URL.

## Troubleshooting

| Problem | Fix |
| ------- | --- |
| `extension "vector" is not available` | Install pgvector on the PostgreSQL server, or use a provider such as Supabase/Neon. |
| `DATABASE_URL is not set` | Make sure `.env` is in the project root and contains `DATABASE_URL`. |
| `password authentication failed` | URL-encode special characters in the password (`@` → `%40`, `#` → `%23`, ...). |
| `relation "intellentx_docs" does not exist` | Call `POST /init` before asking questions. |
| First request is very slow | The embedding model is downloaded once on first ingest/query; later requests are faster. |
| Groq `401` / `invalid_api_key` | Check `GROQ_API_KEY` in `.env` and restart the API. |
| UI says "Backend returned HTTP ... not JSON" | The API is not running or `BACKEND_URL` is wrong. Start the API first. |
| Port already in use | Change the API port with `--port 8001` and set `BACKEND_URL` accordingly, or change `PORT` for the UI. |
