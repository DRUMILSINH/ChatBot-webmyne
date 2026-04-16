# Build Chatbot From Scratch: Master Guide (Generic + This Repo, Local-First)

## Purpose and Audience
This document is for developer onboarding and local-first delivery.
It serves two goals in this order:
1. Show a generic blueprint for building a chatbot from scratch.
2. Map that blueprint to this repository so you can verify what is already provided and what must be installed/provided externally.

## Quick Architecture Map of This Project
Current stack in this repo:
- Backend: Django (`chatbot_ui`, `chat`)
- RAG pipeline: crawler + chunking + embeddings + retrieval (`chatbot`)
- Vector DB: Chroma persistent directories under `db/<vector_id>/`
- LLM runtime: Ollama (default model behavior is `mistral`)
- Frontend: React + Vite sidecar (`frontend/`)
- Legacy UI: Django template + static JS (`chat/templates/chat/chat.html`, `chat/static/chat/chat.js`)

Request flow (v2):
1. Frontend calls `/api/v2/...`.
2. `chat/views_v2.py` validates, manages sessions/messages, and streams SSE.
3. `chat/services_v2.py` executes secure retrieval + generation.
4. `chatbot/retrieval.py` does hybrid dense/sparse retrieval and optional rerank.
5. Ollama generates answer, response is sanitized and returned with sources/debug metadata.

## Do We Have Everything? Readiness Matrix
| Requirement | Why Needed | Present in Repo | Must Be Provided Externally | Verification Command / Check |
|---|---|---|---|---|
| Django backend source | API, session, routing, models | Yes | No | `Test-Path .\manage.py` |
| Chat/RAG code modules | Crawl, retrieval, prompting, LLM calls | Yes | No | `Test-Path .\chatbot\utils.py` |
| Frontend sidecar | Modern chat UI and SSE client | Yes | No | `Test-Path .\frontend\package.json` |
| Python dependency manifest | Reproducible backend install | Yes | No | `Test-Path .\requirements.txt` |
| Node dependency manifest | Reproducible frontend install | Yes | No | `Test-Path .\frontend\package.json` |
| Database migrations | Schema creation | Yes | No | `Get-ChildItem .\chat\migrations` |
| Legacy + v2 API routes | Runtime endpoints | Yes | No | Check `chat/urls.py` and `chat/urls_v2.py` |
| Ollama runtime | Local LLM inference | No | Yes | `ollama --version` |
| `mistral` model in Ollama | Default generation model | No | Yes | `ollama list` |
| Chrome/Chromium | Selenium crawling target browser | No | Yes | Launch check: `chrome --version` or installed Chrome in PATH |
| Internet for first-time model/dependency downloads | Pull Python/Node/model assets and driver binaries | No | Yes | `Invoke-WebRequest https://huggingface.co -Method Head` |
| `.env.example` template | Standardized local config onboarding | No | Yes (should be added) | `Test-Path .\.env.example` (currently false) |
| Root `README.md` | Primary project entrypoint | No | Yes (should be added) | `Get-ChildItem -Name README*` (currently empty) |

## External Prerequisites Checklist
Install/verify before setup:
- Python 3.10+ (recommended 3.11/3.12)
- Node.js 18+ and npm
- Ollama runtime
- Ollama model `mistral` (`ollama pull mistral`)
- Google Chrome (for Selenium crawler paths)
- Internet access (first-time package/model/download steps)

Suggested checks (PowerShell):

```powershell
python --version
node -v
npm -v
ollama --version
ollama list
```

## Environment/Config Checklist
Settings are loaded from `chatbot_ui/settings.py`. Most flags have local-safe defaults, but production should set explicit values.

Core Django/env:
- `DJANGO_SECRET_KEY` (default: `django-insecure-local-dev-only`)
- `DJANGO_DEBUG` (default: `True`)
- `DJANGO_ALLOWED_HOSTS` (default: `127.0.0.1,localhost,*`)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (default: empty)
- `DJANGO_TIME_ZONE` (default: `UTC`)

Logs DB/env:
- `LOGS_DB_ENGINE` (default: `django.db.backends.sqlite3`)
- If non-SQLite logs DB:
  - `LOGS_DB_NAME` (default: `chatbot_db`)
  - `LOGS_DB_USER` (default: `openpg`)
  - `LOGS_DB_PASSWORD` (default: `openpgpwd`)
  - `LOGS_DB_HOST` (default: `localhost`)
  - `LOGS_DB_PORT` (default: `5432`)

Security/session/runtime:
- `SESSION_COOKIE_AGE` (default: `3600`)
- `SESSION_COOKIE_SAMESITE` (default: `Lax`)
- `CSRF_COOKIE_SAMESITE` (default: `Lax`)
- `ENFORCE_RBAC` (default: `False`)
- `SAFE_BLOCK_MESSAGE` (default provided in settings)

Crawl policy/queue:
- `CRAWL_DOMAIN_ALLOWLIST` (JSON, default: `{}`)
- `CRAWL_MAX_PAGES` (default: `20`)
- `CRAWL_VALIDATE_REDIRECTS` (default: `True`)
- `CRAWL_REQUIRE_ALLOWLIST` (default: `False`)
- `MAX_JOBS_PER_USER` (default: `5`)
- `MAX_QUEUE_SIZE` (default: `100`)
- `MAX_PARALLEL_CRAWL_WORKERS` (default: `4`)

RAG/retrieval controls:
- `RAG_DENSE_K` (default: `30`)
- `RAG_BM25_K` (default: `30`)
- `RAG_TOP_K` (default: `8`)
- `RAG_MIN_TOP_K` (default: `4`)
- `RAG_MAX_CONTEXT_CHARS` (default: `9000`)
- `ENABLE_RERANKER` (default: `False`)
- `RERANKER_MODEL` (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- `RAG_LATENCY_KILL_SWITCH_MS` (default: `1500`)
- `RAG_ADAPTIVE_DISABLE_TTL_SEC` (default: `60`)
- `MIN_CONFIDENCE_TO_ANSWER` (default: `0.25`)
- `ENABLE_QUERY_CACHE` (default: `True`)
- `QUERY_CACHE_TTL_SEC` (default: `120`)
- `ENABLE_RETRIEVAL_CACHE` (default: `True`)
- `RETRIEVAL_CACHE_TTL_SEC` (default: `60`)

Streaming/load controls:
- `SSE_REQUIRE_ASGI` (default: `True`)
- `MAX_CONCURRENT_STREAMS` (default: `50`)
- `HIGH_LOAD_STREAM_THRESHOLD` (default: `20`)
- `HIGH_LOAD_QUEUE_THRESHOLD` (default: `40`)

Warmup:
- `ENABLE_COLD_START_PRELOAD` (default: `False`)
- `PRELOAD_VECTOR_IDS` (default: empty)

Missing artifacts to add later:
- `.env.example` (not present)
- root `README.md` (not present)

## Local Setup Steps (PowerShell-First)
1. Create and activate virtual environment.

```powershell
cd C:\Users\DELL5.000\Downloads\chatbot\chatbot
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Install frontend dependencies.

```powershell
cd .\frontend
npm install
cd ..
```

3. Start/pull Ollama model (separate terminal recommended).

```powershell
ollama pull mistral
ollama serve
```

4. Run migrations for both databases (required due DB router behavior).

```powershell
python manage.py migrate --database=default
python manage.py migrate --database=logs
```

5. Start backend with ASGI (recommended for SSE endpoint).

```powershell
uvicorn chatbot_ui.asgi:application --host 127.0.0.1 --port 8000 --workers 1
```

6. Start frontend (new terminal).

```powershell
cd .\frontend
npm run dev
```

Optional Linux/macOS equivalents:
- Activate venv: `source .venv/bin/activate`
- Same Python/npm/uvicorn commands otherwise.

## Data Ingestion Steps
You can ingest knowledge by legacy sync API or v2 async crawl-jobs API.

### Legacy ingest (`/api/crawl/`)
Use when you want direct crawl+embed in one request.

```powershell
$body = @{
  url = "https://example.com"
  vector_id = "webmyne"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/crawl/" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### v2 ingest (`/api/v2/crawl/jobs`)
Use when you want async queue/job tracking.
Important: this endpoint is `chat_admin` role-protected (`force=True`), so you need an authenticated user with that role.

Create job:

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Bootstrap CSRF
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v2/auth/csrf" -WebSession $session | Out-Null
$csrf = ($session.Cookies.GetCookies("http://127.0.0.1:8000") | Where-Object { $_.Name -eq "csrftoken" }).Value

$body = @{ vector_id = "webmyne"; url = "https://example.com" } | ConvertTo-Json
$headers = @{ "X-CSRFToken" = $csrf }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v2/crawl/jobs" `
  -Method Post `
  -WebSession $session `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Poll job status:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/crawl/jobs/<job_uuid>" -WebSession $session
```

## Existing API Contracts (Payload Examples)
No runtime API changes are introduced by this document.

### 1) `POST /api/chat/`
Purpose: legacy chat answer.

Request:

```json
{
  "query": "What services do you provide?",
  "vector_id": "webmyne"
}
```

Success `200`:

```json
{
  "answer": "....",
  "sources": [
    {
      "url": "https://example.com/page",
      "chunk_id": "https://example.com/page_chunk_0",
      "md5": "abc123",
      "content": "text...",
      "note": "verified"
    }
  ]
}
```

Common errors:
- `400` missing `query`/`vector_id`
- `405` non-POST
- `500` internal failure

### 2) `POST /api/crawl/`
Purpose: legacy crawl + embed.

Request:

```json
{
  "url": "https://example.com",
  "vector_id": "webmyne"
}
```

Success `200`:

```json
{
  "status": "success",
  "message": "Website crawled and embedded successfully for vector_id: webmyne"
}
```

Common errors:
- `400` missing fields
- `405` non-POST
- `500` pipeline/security failure

### 3) `GET|POST /api/v2/chats`
Purpose: list or create chat sessions.

Create request (`POST`):

```json
{
  "vector_id": "webmyne",
  "title": "My Chat"
}
```

Create success `201`:

```json
{
  "chat": {
    "id": "uuid",
    "title": "My Chat",
    "vector_id": "webmyne",
    "is_archived": false,
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
}
```

List success `200`:

```json
{
  "items": []
}
```

### 4) `GET|POST /api/v2/chats/<uuid>/messages`
Purpose: list messages or send query.

Send request (`POST`):

```json
{
  "query": "What services do you provide?",
  "vector_id": "webmyne"
}
```

Success `200`:

```json
{
  "chat_session_id": "uuid",
  "user_message_id": 1,
  "assistant_message_id": 2,
  "answer": "....",
  "sources": [],
  "confidence": 0.8,
  "token_usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  },
  "model_info": {
    "model": "mistral"
  },
  "latency_ms": {
    "total": 120,
    "retrieval": 70,
    "generation": 50
  }
}
```

### 5) `POST /api/v2/chat/stream`
Purpose: SSE token streaming chat.

Request:

```json
{
  "chat_session_id": "optional-uuid",
  "vector_id": "webmyne",
  "query": "Tell me about your company."
}
```

Success `200` with `Content-Type: text/event-stream` emits:
- `event: start`
- `event: token`
- `event: done`

Example stream frames:

```text
event: start
data: {"trace_id":"...","chat_session_id":"...","user_message_id":1}

event: token
data: {"token":"Hello "}

event: done
data: {"assistant_message_id":2,"answer":"Hello world","sources":[],"confidence":0.5,"token_usage":{"prompt_tokens":2,"completion_tokens":2,"total_tokens":4},"model_info":{"model":"mistral"},"latency_ms":{"total":5,"retrieval":2,"generation":3}}
```

Common errors:
- `400` missing query/vector_id or invalid JSON
- `429` stream capacity reached
- `503` SSE attempted under WSGI when `SSE_REQUIRE_ASGI=true`

### 6) `POST /api/v2/crawl/jobs`
Purpose: create async crawl job.

Request:

```json
{
  "vector_id": "webmyne",
  "url": "https://example.com"
}
```

Success `202`:

```json
{
  "job_id": "uuid",
  "status": "queued",
  "vector_id": "webmyne",
  "url": "https://example.com",
  "created_at": "ISO8601"
}
```

Common errors:
- `403` blocked by URL/allowlist security checks or missing role
- `429` queue full or per-user quota exceeded

## Smoke Test Steps
1. Validate clean setup commands.
- Run prerequisites checks.
- Run install/migration/startup commands from this guide.

2. Run backend tests.

```powershell
python manage.py test chat
```

3. Execute API smoke tests.

Legacy chat API:

```powershell
$body = @{ query = "What services do you provide?"; vector_id = "webmyne" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat/" -Method Post -ContentType "application/json" -Body $body
```

v2 create session:

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v2/auth/csrf" -WebSession $session | Out-Null
$csrf = ($session.Cookies.GetCookies("http://127.0.0.1:8000") | Where-Object { $_.Name -eq "csrftoken" }).Value
$headers = @{ "X-CSRFToken" = $csrf }
$create = @{ vector_id = "webmyne"; title = "Smoke Chat" } | ConvertTo-Json

$chat = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v2/chats" `
  -Method Post `
  -WebSession $session `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $create

$chat
```

v2 send message:

```powershell
$chatId = $chat.chat.id
$msgBody = @{ query = "What does this company do?" } | ConvertTo-Json
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v2/chats/$chatId/messages" `
  -Method Post `
  -WebSession $session `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $msgBody
```

SSE stream test (ASGI backend running):

```powershell
curl.exe -N -X POST "http://127.0.0.1:8000/api/v2/chat/stream" `
  -H "Content-Type: application/json" `
  -d "{\"vector_id\":\"webmyne\",\"query\":\"hello\"}"
```

4. Verify frontend proxy behavior.
- Start Vite: `npm run dev` in `frontend`.
- Open `http://127.0.0.1:5173`.
- Confirm frontend can load chats and receive streamed answer from `/api/v2/chat/stream` via Vite proxy to Django.

## Troubleshooting
### Missing model/runtime
Symptoms:
- errors like model unavailable, failed generation, or Ollama not found.
Fix:
1. `ollama --version`
2. `ollama pull mistral`
3. Ensure `ollama serve` is running.

### DB router/migration mismatch
Symptoms:
- `chat_*` tables missing or writes failing to logs DB.
Fix:
1. Run both migration commands explicitly:
   - `python manage.py migrate --database=default`
   - `python manage.py migrate --database=logs`
2. Confirm `LOGS_DB_ENGINE` and related `LOGS_DB_*` variables are correct.

### SSE on WSGI returns 503
Symptoms:
- `/api/v2/chat/stream` returns `503` with ASGI requirement message.
Fix:
1. Start backend with ASGI server:
   - `uvicorn chatbot_ui.asgi:application --host 127.0.0.1 --port 8000`
2. Only for temporary non-stream local testing, set `SSE_REQUIRE_ASGI=false`.

### Crawl URL blocked by security allowlist checks
Symptoms:
- crawl endpoints return `403` with validation/allowlist message.
Fix:
1. Check `CRAWL_REQUIRE_ALLOWLIST` and `CRAWL_DOMAIN_ALLOWLIST`.
2. Ensure target domain is allowed for that `vector_id`.
3. Ensure URL resolves to public/non-private IP and redirect chain stays allowlisted.

## Generic From-Scratch Build Sequence
Use this sequence when building a new chatbot project from zero.

1. Scope/use-case:
- define users, query types, languages, latency and quality targets.

2. Data ingestion:
- identify sources (web, docs, DB), crawl/load strategy, freshness policy.

3. Chunk/embedding strategy:
- choose chunk size/overlap, metadata schema, and embedding model.

4. Retrieval + ranking:
- implement dense retrieval, add sparse/BM25 fallback, fusion/rerank if needed.

5. Generation + guardrails:
- set system prompt, citation/link controls, policy checks, refusal behavior.

6. API + UI:
- design session/message contracts, streaming path, error model, frontend state model.

7. Observability and feedback loop:
- log traces, latency, token usage, confidence, user feedback, and retrieval diagnostics.

8. Hardening and deployment:
- auth/RBAC, input/output sanitization, queue/backpressure controls, ASGI scaling, environment templates, CI tests, and runbooks.
