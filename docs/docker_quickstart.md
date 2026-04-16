# Docker quickstart

This project can be run with Docker Compose so your team gets the same runtime, dependencies, and startup steps on every machine.

## What this setup runs

- `backend`: Django + Uvicorn on `http://localhost:8000`
- `frontend`: Vite app on `http://localhost:5173`
- `postgres`: PostgreSQL on `localhost:5432`
- `chroma`: ChromaDB server on `http://localhost:8001` (shared persistent store)

## 1) Start the full stack

1. Ensure Ollama is running on your host:
   - `ollama pull mistral`
   - `ollama serve`
2. From project root, start all services:
   - `docker compose up --build`
3. Open:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - Chroma heartbeat: `http://localhost:8001/api/v1/heartbeat`

By default the backend container points to host Ollama at `http://host.docker.internal:11434`.

## 2) Useful commands

- Reset and rebuild:
  - `docker compose down -v`
  - `docker compose up --build`
- Run Django checks in backend container:
  - `docker compose exec backend python manage.py check`
- Inspect structured JSON logs:
  - `docker compose logs -f backend`

## 3) Stop services

- `docker compose down`

## Why this helps

- One command startup for frontend, backend, Postgres, and Chroma.
- No local Python/Node package drift.
- Consistent environment for every developer.
- Easier onboarding and reproducible troubleshooting.
