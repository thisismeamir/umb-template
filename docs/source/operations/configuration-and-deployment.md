# Configuration & Deployment

## Environment Variable Reference

All backend settings are loaded by `app/config.py` (`pydantic-settings`) from process environment variables or `.env`:

| Variable | Default | Description |
|---|---|---|
| `METADATA_BROWSER_POSTGRES_USER` | `admin` | PostgreSQL username |
| `METADATA_BROWSER_POSTGRES_PASSWORD` | `admin` | PostgreSQL password |
| `METADATA_BROWSER_POSTGRES_DB` | `postgres` | PostgreSQL database name |
| `METADATA_BROWSER_POSTGRES_HOST` | `localhost` | PostgreSQL host (`postgres` in Compose) |
| `METADATA_BROWSER_POSTGRES_PORT` | `5432` | PostgreSQL port |
| `METADATA_BROWSER_REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL (`redis://redis:6379/0` in Compose) |
| `METADATA_BROWSER_AUTH_ENABLED` | `false` | Set `true` to enforce Bearer JWT auth |
| `METADATA_BROWSER_APPLICATION_SECRET_KEY` | `dev-insecure-change-me` | HS256 JWT signing secret (**must be rotated in prod**) |
| `METADATA_BROWSER_FRONTEND_HOST` | `0.0.0.0` | Nuxt server bind address |
| `METADATA_BROWSER_FRONTEND_URL` | `http://localhost:3000` | Frontend origin URL |
| `METADATA_BROWSER_LOG_LEVEL` | `INFO` | Logging verbosity |

## Production Deployment Checklist

- **Rotate `METADATA_BROWSER_APPLICATION_SECRET_KEY`** to a high-entropy 32+ byte secret and set `METADATA_BROWSER_AUTH_ENABLED=true`.
- **Keep `databaseResetOnStartup = False`** (the default): `DatabaseInitializer` acquires a PostgreSQL advisory lock (`databaseSchemaAdvisoryLock`) and runs idempotent `CREATE TABLE IF NOT EXISTS` statements so multi-worker restarts never drop data.
- **Enable Redis AOF persistence**: `docker-compose.yml` launches Redis with `redis-server --appendonly yes` mounted to `redis-data:/data` so queued jobs survive Redis restarts.
- **Scale `JobWorker` horizontally**: You can run multiple `worker` replicas (`docker compose up -d --scale worker=4`) safely because `BLMOVE` claims each job ID atomically.

## Deploying Documentation on Read the Docs

This repository ships with `.readthedocs.yaml` (v2) at the repository root and uses the default `sphinx_rtd_theme`:

1. Sign in to [readthedocs.org](https://readthedocs.org) and import `thisismeamir/umb-template`.
2. Read the Docs automatically detects `.readthedocs.yaml`, installs `docs/requirements.txt` on Python 3.12 (`ubuntu-24.04`), and builds `docs/source/conf.py`.
3. Every push to `main` (and PR previews if enabled) rebuilds and publishes the documentation automatically.
