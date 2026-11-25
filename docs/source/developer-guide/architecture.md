# System Architecture

UMB follows a strict layered architecture across its FastAPI backend, Redis async worker, PostgreSQL JSONB database, and Nuxt 3 frontend.

## Backend Layer Map

```text
backend/app/
├── main.py                  # Lifespan (DB pool, Redis queue, FileWatcher), CORS/Timing/Logging middleware
├── config.py                # Typed pydantic-settings configuration reading .env
├── api/
│   ├── dependencies.py      # Api lifecycle container + Provider DI factories (module-level callables)
│   ├── middleware/          # TimingMiddleware (X-Process-Time, X-Request-Id), RequestLoggingMiddleware
│   └── v1/                  # Mounted sub-app at /api/v1 (8 domains + HealthRouter)
├── models/                  # Pydantic v2 request/response contracts per domain
├── engine/                  # Pure, stateless logic (no HTTP, no DB)
│   ├── entry/               # EntityEngine, ANTLR4 grammar + ExpressionHandler, SQLPlanner
│   ├── search/              # SearchEngine (fulltext, similarity, suggest)
│   ├── analytics/           # AnalyticsEngine (histogram, summary, compare, coverage)
│   ├── export/              # ExportFormatters (CSV, JSON, YAML, TOML, Python — stdlib only)
│   └── auth/                # TokenEngine (stdlib RFC 7519 HS256 JWT)
├── services/                # Domain orchestration + EntityRequestValidator
├── repositories/            # Parameterized asyncpg SQL access (entry, navigation, collections, jobs)
├── database/                # schema.sql + advisory-locked idempotent DatabaseInitializer
└── workers/                 # FileWatcher, RedisJobQueue, JobRegistry, standalone JobWorker
```

## Request Execution Pipeline

1. **Middleware** (`TimingMiddleware` + `RequestLoggingMiddleware` + `CORSMiddleware`) wraps every request.
2. **Router** (`api/v1/<domain>/router.py`) parses and validates Pydantic models, then resolves dependencies via `Provider`.
3. **Service** (`services/<domain>/`) runs semantic validation (`EntityRequestValidator` or ACL checks), invokes pure **Engines**, and queries **Repositories**.
4. **SQLPlanner** builds parameterized `?` fragments and converts all placeholders to PostgreSQL `$1, $2, ...` in a single top-level `_bindPlaceholders()` pass.

## Durable Async Job Architecture (`RedisJobQueue` + `JobWorker`)

To guarantee that long-running exports and analytics jobs survive API or worker restarts:

1. `POST /api/v1/jobs/` inserts a `pending` row in PostgreSQL `jobs` and pushes `job_id` onto Redis (`LPUSH umb:jobs:queue <job_id>`).
2. `JobWorker` (`python -m app.workers.JobWorker`) atomically claims jobs with `BLMOVE umb:jobs:queue umb:jobs:processing RIGHT LEFT`.
3. While running, `job_id` remains in `umb:jobs:processing`. On completion or failure, `JobWorker` updates PostgreSQL (`done`/`failed` + JSONB `result`/`error`) and removes `job_id` via `LREM` (`ack()`).
4. If a worker crashes mid-job, the next worker calls `recoverOrphaned()` on startup, moving any stranded IDs from `umb:jobs:processing` back to `umb:jobs:queue` and resetting their DB status to `pending`.

## Frontend Architecture

The Nuxt 3 frontend (`frontend/`) centralizes all HTTP traffic in `composables/api/useApiClient.ts` and `types/api.ts`, targeting `/api/v1/*` with automatic Bearer JWT attachment and `401` refresh via `POST /api/v1/auth/refresh`.
