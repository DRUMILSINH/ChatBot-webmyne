# AI Control Center Chatbot

A full-stack, local-first RAG chatbot platform built with Django + React.

It crawls website content, stores embeddings in Chroma, retrieves relevant chunks, and generates grounded answers with Ollama.

## What This Project Includes

- Django backend with v2 chat APIs and SSE streaming
- React + Vite frontend sidecar (`frontend/`)
- Legacy Django template chat UI (`chat/templates/chat/chat.html`)
- Hybrid retrieval pipeline (dense + BM25 fusion, optional reranker)
- Tenant-style vector collections via `vector_id`
- Safety and observability layers (input/output policy checks, trace/audit logging)

## Tech Stack

- Backend: Django 5, Uvicorn (ASGI)
- Frontend: React 18, Vite, TypeScript, Zustand, React Query
- LLM runtime: Ollama (`mistral` by default)
- Vector store: Chroma (local persistent directories)
- Databases: SQLite or PostgreSQL (configurable for both `default` and `logs` DBs)

## Architecture

1. Frontend sends chat request to `/api/v2/...`
2. Backend validates request, session, and policy checks
3. Retrieval pipeline loads `db/<vector_id>/` collection
4. Hybrid retriever returns top chunks
5. Ollama generates answer from retrieved context
6. Backend returns answer, sources, confidence, tokens, and latency metadata

## Repository Layout

- `chatbot_ui/` Django settings and root URL config
- `chat/` API views, models, security, RBAC, observability
- `chatbot/` crawling, chunking, vector-store + retrieval pipeline
- `frontend/` React sidecar UI
- `db/` persisted Chroma collections (`db/<vector_id>/chroma.sqlite3`)
- `docs/` deployment and upgrade guides

## Prerequisites

- Python 3.12+ (recommended)
- Node.js 20+ (recommended)
- Docker + Docker Compose (for containerized run)
- Ollama installed and running on host machine
- Chrome/Chromium installed (required for Selenium-based crawling)
- Ollama model pulled locally:

```bash
ollama pull mistral
ollama serve
```

## Quick Start (Docker)

1. Start Ollama on the host machine:

```bash
ollama pull mistral
ollama serve
```

2. From project root, run:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Chroma heartbeat: `http://localhost:8001/api/v1/heartbeat`

4. Stop services:

```bash
docker compose down
```

## Local Development (Without Docker)

### 1) Backend setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) Run migrations (both databases)

```bash
python manage.py migrate --database=default
python manage.py migrate --database=logs
```

### 3) Start backend with ASGI (required for streaming)

```bash
uvicorn chatbot_ui.asgi:application --host 127.0.0.1 --port 8000 --workers 1
```

### 4) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173` and proxies `/api/v2` to `http://127.0.0.1:8000` by default.

## API Routes

### v2 routes (enabled by default)

Base prefix: `/api/v2/`

- `GET /auth/csrf`
- `GET|POST /chats`
- `GET|POST /chats/<uuid>/messages`
- `POST /chat/stream` (SSE)
- `POST /chat/feedback`
- `GET /chat/debug/<message_id>`
- `GET /knowledge-base/stats/?vector_id=<id>`

### Legacy routes (disabled by default)

Legacy endpoints are only mounted when `ENABLE_LEGACY_CHAT_ROUTES=true`.

Mounted prefixes then include `/api/`, `/chat/`, and `/` for legacy views such as:

- `POST /api/chat/`
- `POST /api/crawl/`
- `POST /api/log-click/`

## Important Configuration

Set through environment variables in `chatbot_ui/settings.py`.

- `DJANGO_DEBUG` (default: `true`)
- `DJANGO_SECRET_KEY`
- `API_V2_PREFIX` (default: `api/v2`)
- `ENABLE_LEGACY_CHAT_ROUTES` (default: `false`)
- `SSE_REQUIRE_ASGI` (default: `true`)
- `OLLAMA_MODEL` (default: `mistral`)
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `CHROMA_PERSIST_ROOT` (default: `<repo>/db`)
- `DEFAULT_DB_*` and `LOGS_DB_*` for DB engine/host/name/user/password/port
- `ENFORCE_RBAC` to enforce role-based access globally

## Roles and Access

The app creates these groups after migrations:

- `chat_user`
- `chat_analyst`
- `chat_admin`

`/api/v2/chat/debug/<message_id>` is role-protected (`chat_analyst` or `chat_admin`) and also allows superusers.

## Testing

Run backend tests:

```bash
python manage.py test chat
```

## Troubleshooting

- Streaming returns `503`: run backend under ASGI (`uvicorn`), or set `SSE_REQUIRE_ASGI=false` for non-stream local testing.
- Model errors: ensure `ollama serve` is running and `mistral` is pulled.
- Missing chat tables/log write issues: run migrations for both DB aliases (`default` and `logs`).
- Legacy API not found: set `ENABLE_LEGACY_CHAT_ROUTES=true` and restart backend.

## Additional Docs

- `docs/docker_quickstart.md`
- `docs/streaming_deployment.md`
- `docs/production_upgrade.md`
- `docs/project_explanation.md`
