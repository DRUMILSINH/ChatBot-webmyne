# Production Upgrade (Incremental v2)

This repository now includes additive production-oriented upgrades while preserving legacy routes.

## Backend v2 APIs

Base prefix: `/api/v2/`

- `GET /auth/csrf` - bootstrap CSRF cookie.
- `GET /chats` - list chat sessions.
- `POST /chats` - create a chat session.
- `GET /chats/<uuid>/messages` - list chat messages.
- `POST /chats/<uuid>/messages` - send non-stream message.
- `POST /chat/stream` - SSE response stream (`start`, `token`, `done` events).
- `POST /chat/feedback` - user thumbs up/down + correction logging.
- `GET /chat/debug/<message_id>` - debug payload (retrieval/docs/token/model metadata).
- `POST /crawl/jobs` - create async crawl job.
- `GET /crawl/jobs/<uuid>` - poll crawl job status.

Legacy routes under `/api/` and `/chat/` are unchanged.

## New Data Models

- `ChatSession`
- `ChatMessage`
- `AuditLog`
- `CrawlJob`

## Security / Safety Additions

- Request trace IDs via `X-Trace-Id` middleware.
- Input/output policy checks and sanitization in v2 service flow.
- URL/domain and private-network crawl target validation (DNS/IP + redirect-chain checks).
- Optional RBAC enforcement via `ENFORCE_RBAC`.
- Tamper-evident audit logs with hash chaining (`prev_hash`, `entry_hash`).

## RAG Improvements

- Hybrid retrieval (dense + BM25 fallback).
- Reciprocal-rank fusion.
- Optional cross-encoder reranking (`ENABLE_RERANKER`).
- Context compression and confidence scoring.
- Adaptive latency kill-switches and query/retrieval caches.
- Grounding score based on retrieval overlap, rerank margin, and citation coverage.

## Frontend Sidecar

React sidecar scaffold exists in `frontend/` with:

- chat bubbles
- SSE streaming UI
- chat history sidebar + new chat
- dark mode
- responsive layout
- developer debug panel

## Environment Flags

Configured in `chatbot_ui/settings.py`:

- `ENFORCE_RBAC`
- `CRAWL_DOMAIN_ALLOWLIST` (JSON)
- `CRAWL_REQUIRE_ALLOWLIST`, `CRAWL_VALIDATE_REDIRECTS`
- `MAX_JOBS_PER_USER`, `MAX_QUEUE_SIZE`, `MAX_PARALLEL_CRAWL_WORKERS`
- `SSE_REQUIRE_ASGI`, `MAX_CONCURRENT_STREAMS`
- `RAG_DENSE_K`, `RAG_BM25_K`, `RAG_TOP_K`
- `RAG_MIN_TOP_K`, `RAG_LATENCY_KILL_SWITCH_MS`
- `ENABLE_RERANKER`, `RERANKER_MODEL`
- `ENABLE_QUERY_CACHE`, `QUERY_CACHE_TTL_SEC`
- `ENABLE_RETRIEVAL_CACHE`, `RETRIEVAL_CACHE_TTL_SEC`
- `MIN_CONFIDENCE_TO_ANSWER`
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, DB env vars
