# Quickstart Guide

This guide gets a full UMB stack (PostgreSQL, Redis, FastAPI backend, async `JobWorker`, and Nuxt 3 frontend) running locally with Docker Compose.

## Prerequisites

- Docker or Podman with Compose v2 (`docker compose`)
- Optional for local development: Python 3.12+ with `uv`, Node.js 22+ with `yarn`

## 1. Configure Environment Variables

Copy the template environment file at the repository root and customize secrets before production use:

```bash
cp .env.example .env
```

Key defaults in `.env.example`:

- `METADATA_BROWSER_POSTGRES_USER=admin`
- `METADATA_BROWSER_POSTGRES_PASSWORD=admin`
- `METADATA_BROWSER_POSTGRES_DB=postgres`
- `METADATA_BROWSER_REDIS_URL=redis://localhost:6379/0` (overridden to `redis://redis:6379/0` inside Docker Compose)
- `METADATA_BROWSER_AUTH_ENABLED=false` (set to `true` to require Bearer JWT tokens)

## 2. Start the Stack

```bash
docker compose up --build -d
```

Docker Compose waits for PostgreSQL (`pg_isready`) and Redis (`redis-cli ping`) health checks before starting `backend` and `worker`.

| Service | Default URL | Purpose |
|---|---|---|
| Frontend (Nuxt 3) | `http://localhost:3000` | Interactive browser UI |
| Backend API v1 | `http://localhost:8000/api/v1` | REST & DSL API |
| Interactive Swagger UI | `http://localhost:8000/api/v1/docs` | OpenAPI v1 explorer |
| Health Check | `http://localhost:8000/api/v1/check/` | Readiness & version check |

## 3. Ingest Sample Metadata

UMB's `FileWatcher` monitors `backend/app/storage/data/` (mounted to `/data` in Docker) for JSON batch files named:

```text
<entry_type>__<source>__<created_by>.json
```

Drop a JSON array file into `backend/app/storage/data/`:

```bash
cp samplejsons/sample_TOOL_kid-a.json \
   backend/app/storage/data/collision__DIRAC__amir.json
```

Within ~2 seconds, `FileWatcher` inserts each item into `entries`, populates `field_registry` with discovered keys and value types, and moves the file into `backend/app/storage/data/processed/`. On restart, already-processed files in `processed/` are not re-ingested.

## 4. Run Your First Query

```bash
curl -s http://localhost:8000/api/v1/entity/ \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "collision",
    "take": { "name": {}, "process": {} },
    "get": { "first": 5 }
  }' | jq
```
