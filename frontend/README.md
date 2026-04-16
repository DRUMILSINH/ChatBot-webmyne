# Chatbot UI v2 (React Sidecar)

## Run locally

1. Install dependencies:
   npm install
2. Start Django backend at `http://127.0.0.1:8000`
3. Start frontend:
   npm run dev

Vite proxies `/api` and `/chat` requests to Django.
You can override the proxy target with:

`VITE_API_PROXY_TARGET=http://backend:8000 npm run dev`

## Features

- Streaming chat (`/api/v2/chat/stream`)
- Sidebar chat history
- New chat creation
- Dark mode persistence
- Debug panel (retrieved docs, links, confidence, tokens, model info)
