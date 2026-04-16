# Streaming Deployment Guidance (ASGI)

The SSE endpoint `/api/v2/chat/stream` is protected by `SSE_REQUIRE_ASGI`.

If the app runs under WSGI, streaming returns `503` to avoid worker starvation.

## Recommended runtime

- Run Django with ASGI server:
  - `uvicorn chatbot_ui.asgi:application --host 0.0.0.0 --port 8000 --workers 4`
  - or `daphne chatbot_ui.asgi:application`

## Key controls

- `SSE_REQUIRE_ASGI=true`
- `MAX_CONCURRENT_STREAMS=50`
- `HIGH_LOAD_STREAM_THRESHOLD=20`
- `HIGH_LOAD_QUEUE_THRESHOLD=40`

## Why this matters

- WSGI + long-lived SSE ties up worker threads.
- Under load, this causes request queueing and degraded latency.
- ASGI allows non-blocking connection handling and safer scaling.
