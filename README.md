# UMB Backend — Project Documentation

---

## 1. README

> Intended as a replacement for the current `backend/` README.

---

# Universal Metadata Browser — Backend

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)

A modular, domain-driven FastAPI backend for the Universal Metadata Browser — a searchable metadata catalog platform originally built for HEP/FCC physics event data at CERN.

This backend powers browse, search, query, analytics, and export over structured scientific metadata stored in PostgreSQL.

---

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                │
│        api/v1/{domain}/router.py + middleware        │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                 Service Layer                        │
│         services/{domain}_service.py                │
└────┬───────────────┬──────────────────┬─────────────┘
     │               │                  │
┌────▼────┐   ┌──────▼──────┐   ┌──────▼──────┐
│ Engine  │   │ Repository  │   │   Workers   │
│(business│   │(data access)│   │ (bg tasks)  │
│ logic)  │   │             │   │             │
└────┬────┘   └──────┬──────┘   └─────────────┘
     │               │
┌────▼───────────────▼────────────────────────────────┐
│                 Storage Layer                        │
│     PostgreSQL (SQLAlchemy ORM) + JSON data files    │
└─────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                 Models Layer                         │
│        models/{domain}/*.py (Pydantic v2)            │
└─────────────────────────────────────────────────────┘
```

---

### Domain Coverage

| Domain | API Routes | Service | Engine |
|---|---|---|---|
| Events | list, detail, bulk, query | `event_service` | `event_query_engine` |
| Collections | list, create, detail, membership | `collection_service` | — |
| Analytics | summary, histogram, compare, coverage | `analytics_service` | `*_engine` |
| Search | fulltext, similar, suggest | `search_service` | `fulltext/similarity/suggest_engine` |
| Export | CSV, JSON, YAML, TOML, Python | `export_service` | `*_formatter` |
| Jobs | submit, status, result | `job_service` | — |
| Navigation | accelerators, campaigns, detectors | `navigation_service` | — |
| Auth | login, token refresh | — | — |

---

### Key Features

- **Custom Query Language (GCLQL)**: field-specific operators, regex, fuzzy matching, and filter compilation via `engine/query/`
- **Multi-format Export**: scientific data output to CSV, JSON, YAML, TOML, and Python dict/pickle formats
- **Background Workers**: async task queue for long-running analytics, import, and export jobs via `workers/`
- **File Watcher**: automatic detection and import of new JSON data files dropped into the `storage/data/` directory
- **Hierarchical Navigation**: physics-native hierarchy — Accelerators → Campaigns → Detectors → Stages
- **CERN SSO / OIDC Auth**: optional JWT-based authentication, fully disableable for public deployments
- **Similarity & Full-text Search**: multi-engine search over metadata fields

---

### Quick Start

**Prerequisites**: Docker / Podman with Compose support.

```bash
# 1. Clone
git clone https://github.com/thisismeamir/umb-template.git
cd umb-template

# 2. Configure
cp .env.example .env        # Edit with your DB credentials, auth settings
cp .envfile.example .envfile

# 3. Start
docker-compose up --build -d

# 4. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

### Configuration

The backend is configured entirely through environment variables (or `.env`). The `config.conf` (HOCON format) provides structural defaults — navigation order, feature flags — and should rarely need editing.

Key environment variables:

| Variable | Description |
|---|---|
| `METADATA_BROWSER_AUTH_ENABLED` | `"true"` / `"false"` |
| `METADATA_BROWSER_CERN_CLIENT_ID` | OIDC client ID (if auth enabled) |
| `METADATA_BROWSER_DB_*` | Database connection settings |
| `METADATA_BROWSER_APPLICATION_SECRET_KEY` | JWT signing secret |

---

### Development

```bash
cd backend
uv sync                   # Install dependencies
ruff check                # Lint
ruff format               # Format
```

---

### Schema Requirements

Your main entity table must include these system columns:

```sql
name          VARCHAR NOT NULL,
uuid          UUID PRIMARY KEY,
created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
metadata      JSONB
```

Navigation foreign keys must follow the pattern `{category}_id`, and the `navigation.order` in `config.conf` must list the names without the `_id` suffix.

---

## 2. Current State of the Project

The backend is currently in the **middle of an active architectural refactor** — transitioning from a minimal monolithic prototype to a clean, domain-driven layered structure.

### What was there (v0 — original template)

The original backend was a 7-directory, 34-file flat prototype:

- A single `storage/database_modules/` folder contained all logic — import, entity retrieval, management, search, and navigation — as monolithic modules.
- Routing was done by three flat router files (`auth_router`, `entities_router`, `navigation_router`) with no versioning.
- No dedicated service, engine, model, or repository layers.
- Utilities were flat `*_utils.py` files with no module organization.
- No background worker system.

This structure worked as a template demo but didn't scale for domain-specific customization or maintainability.

### What exists now (v1 — in-progress refactor)

The project has grown to 54 directories and 238 files. The refactor introduced a proper layered architecture:

**Completed and structured:**
- `models/` — full Pydantic v2 model hierarchy across all domains (events, collections, analytics, auth, jobs, navigation, search, export)
- `repository/` — split read/write data access per domain, with a dedicated `orm/` sublayer containing SQLAlchemy ORM models
- `services/` — one service per domain, acting as the orchestration layer between API and engine/repository
- `engine/` — business logic engines for query compilation, analytics computation, export formatting, and search
- `api/v1/` — versioned API with per-domain route modules, middleware (CORS, logging, timing), and dependency injection via `dependencies.py`
- `workers/` — async background task system with a registry and task modules for analytics, export, and import
- `utils/` — cleaned up and split into typed modules (auth, config, errors, http, logging, pagination, parsing, sql, type_coerce, uuid)

**Still in transition / not fully wired:**
- The old `routers/` directory still exists alongside the new `api/` structure — these are the original flat routers and will eventually be removed
- Some `storage/database_modules/` logic hasn't been fully migrated into the new `repository/` and `engine/` layers
- The `__pycache__` files committed in the tree suggest the refactor is actively being developed locally and hasn't been cleaned up yet
- `utils/` has both old `*_utils.py` names and new clean names (e.g., `auth_utils.py` alongside `auth.py`) — deduplication is pending

### Summary

| Area | Status |
|---|---|
| Models | ✅ Complete |
| Repository layer | ✅ Structured, likely partially implemented |
| Service layer | ✅ Structured, wiring in progress |
| Engine layer | ✅ Structured, implementations ongoing |
| API v1 routes | ✅ Structured |
| Workers / task queue | ✅ Structured |
| Old routers cleanup | ⏳ Pending removal |
| Old database_modules migration | ⏳ Partially migrated |
| Utils deduplication | ⏳ Pending |
| Tests | ❓ Not visible in tree |

---

## 3. Plan & Strategy

### Goal

Transform the UMB template into a robust, maintainable, and extensible backend specifically adapted for HEP/FCC metadata — with clean separation of concerns, testability, and clear onboarding for new contributors.

### Refactoring Strategy

The refactor follows a **bottom-up, domain-by-domain** approach:

1. **Define models first** — Pydantic v2 models provide the contract for every domain before any logic is written. This was the first completed layer.

2. **Repository layer** — Replace the monolithic `storage/database_modules/` with per-domain `repository/{domain}/read.py` and `write.py`, backed by SQLAlchemy ORM models in `repository/orm/`. This decouples data access from business logic entirely.

3. **Engine layer** — Extract all non-trivial computation (query compilation, analytics, search, export formatting) into `engine/`. Engines are pure business logic with no HTTP or DB concerns.

4. **Service layer** — Services in `services/` orchestrate between repositories and engines. They are the single point of entry for each domain, called by API handlers.

5. **API layer** — FastAPI routers in `api/v1/{domain}/` are thin: they validate input (via models), call a service, and return a response. Middleware handles cross-cutting concerns (CORS, logging, timing).

6. **Workers** — Long-running operations (bulk import, analytics over large datasets, export generation) are offloaded to background workers. The `workers/registry.py` tracks task state, and `api/v1/jobs/` exposes status and results.

7. **Cleanup** — Once the new layers are stable, remove `routers/`, deduplicate `utils/`, clean `storage/database_modules/`, and remove `__pycache__` from version control.

### Naming & Structure Conventions

- One module per concern per domain (`read.py` / `write.py`, `router.py`, `*_engine.py`, `*_service.py`)
- ORM models live in `repository/orm/`, never imported directly by services
- All HTTP input/output types live in `models/`, shared across API and service layers
- Engines are stateless and dependency-injection-friendly

### Next Milestones

| Milestone | Description |
|---|---|
| M1 | Complete repository layer for all domains |
| M2 | Wire services to repositories and engines end-to-end |
| M3 | Remove old `routers/` and `database_modules/` |
| M4 | Deduplicate `utils/` |
| M5 | Add integration tests per domain |
| M6 | Document GCLQL query language |

---

## 4. Architecture Explanation

### Layer Map

```
backend/
├── api/              ← HTTP interface
├── engine/           ← Business logic (pure, stateless)
├── models/           ← Data contracts (Pydantic v2)
├── repository/       ← Data access (SQLAlchemy ORM)
├── services/         ← Orchestration (API ↔ Engine ↔ Repo)
├── storage/          ← DB connection, schema, raw data files
├── utils/            ← Cross-cutting helpers
└── workers/          ← Background tasks
```

---

### `api/` — HTTP Interface

The API layer is structured around FastAPI and versioned under `api/v1/`. It is thin by design.

```
api/
├── dependencies.py          # Shared FastAPI dependencies (auth, DB session)
├── middleware/
│   ├── cors.py              # CORS policy
│   ├── logging.py           # Request/response logging
│   └── timing.py            # Response time tracking
└── v1/
    ├── router.py            # Root v1 router, mounts all domain routers
    ├── auth/                # Login + token endpoints
    ├── events/              # Event CRUD, bulk ops, query
    ├── collections/         # Collection management + membership
    ├── analytics/           # Aggregation endpoints
    ├── search/              # Fulltext, similarity, suggestions
    ├── export/              # Multi-format data export
    ├── jobs/                # Async job submission + polling
    ├── navigations/         # Accelerators, campaigns, detectors
    └── builders/            # Query builder helpers
```

Each domain folder contains individual operation files (`list.py`, `detail.py`, `create.py`, etc.) and a `router.py` that assembles them. This keeps each endpoint file focused on a single responsibility.

---

### `models/` — Data Contracts

Pydantic v2 models define the shape of every input, output, and internal data structure. They are the shared language across all layers.

```
models/
├── event/        # EventName, EventQuery, EventResponse
├── collections/  # Collection, Membership
├── analytics/    # Summary, Histogram, Compare
├── auth/         # Credentials, Token, User
├── jobs/         # Job, JobResult
├── navigation/   # Accelerator, Campaign, Detector, Stage
├── search/       # SearchQuery, SearchResponse
├── export/       # ExportFormat
└── common.py     # Shared base types
```

---

### `repository/` — Data Access

The repository layer isolates all database interactions. Each domain has a `read.py` (queries, filters, pagination) and a `write.py` (insert, update, delete). ORM table definitions live in `repository/orm/`.

```
repository/
├── event/
│   ├── read.py      # Event queries
│   ├── write.py     # Event mutations
│   └── mapper.py    # ORM ↔ Pydantic mapping
├── collection/
│   ├── read.py
│   └── write.py
├── job/
│   ├── read.py
│   └── write.py
├── navigation/      # accelerator, campaign, detector, stage
└── orm/             # SQLAlchemy ORM table definitions
    ├── event.py
    ├── collection.py
    ├── job.py
    ├── user.py
    └── navigation/
```

Services never import ORM models directly — they receive and return Pydantic models, and the repository handles all translation.

---

### `engine/` — Business Logic

Engines implement non-trivial computation that doesn't belong in the API or repository. They are pure Python: no HTTP, no DB calls.

```
engine/
├── query/
│   ├── event_query_engine.py   # Orchestrates query execution
│   ├── filter_compiler.py      # Compiles GCLQL filter expressions → SQL
│   ├── option_compiler.py      # Compiles pagination/sort options
│   ├── field_resolver.py       # Resolves field names to DB columns
│   └── plan.py                 # Query execution plan representation
├── analytics/
│   ├── summary_engine.py       # Aggregated field statistics
│   ├── histogram_engine.py     # Value distribution histograms
│   ├── compare_engine.py       # Cross-entity comparisons
│   └── coverage_engine.py      # Field coverage analysis
├── search/
│   ├── fulltext_engine.py      # Full-text search execution
│   ├── similarity_engine.py    # Vector/similarity search
│   └── suggest_engine.py       # Autocomplete suggestions
├── export/
│   ├── csv_formatter.py
│   ├── json_formatter.py
│   ├── yaml_formatter.py
│   ├── toml_formatter.py
│   └── python_formatter.py
└── parsing/
    ├── name_parser.py          # Entity name parsing
    ├── process_parser.py       # Process descriptor parsing
    └── generator_registry.py   # Registered data generator types
```

The `query/` sub-engine is the most complex: it implements the GCLQL custom query language, compiling filter expressions and options into parameterized SQL queries.

---

### `services/` — Orchestration

Services are the single entry point for each domain. They receive Pydantic models from the API, call the appropriate repositories and engines, and return Pydantic models back.

```
services/
├── event_service.py        # Event CRUD + query delegation
├── collection_service.py   # Collection + membership logic
├── analytics_service.py    # Analytics orchestration
├── search_service.py       # Search routing
├── export_service.py       # Export pipeline coordination
├── import_service.py       # Data ingestion from JSON files
├── job_service.py          # Job lifecycle management
├── navigation_service.py   # Hierarchy traversal
└── file_watcher.py         # FS monitor for auto-import
```

---

### `workers/` — Background Tasks

Long-running operations (large exports, bulk analytics, batch imports) are executed asynchronously by the worker system.

```
workers/
├── registry.py          # Task registry: tracks job ID → status/result
├── config.py            # Worker configuration (concurrency, timeouts)
└── tasks/
    ├── analytics_task.py  # Runs analytics engine for a job
    ├── export_task.py     # Runs export formatter for a job
    └── import_task.py     # Runs data import pipeline for a job
```

The `jobs` API domain (`api/v1/jobs/`) exposes submit, status, and result endpoints that interface directly with this worker registry.

---

### `storage/` — Persistence

```
storage/
├── database.py           # SQLAlchemy engine + session factory
├── database.sql          # Schema DDL
├── json_data_model.py    # Pydantic model for raw JSON input files
├── schema_discovery.py   # Runtime schema introspection
├── database_modules/     # (Legacy) monolithic DB logic — being migrated
└── data/                 # Raw JSON data files + tmp import staging
```

The `database_modules/` folder is the original monolithic data layer from the template. Its logic is being progressively migrated into `repository/` and `engine/` and will be removed once migration is complete.

---

### `utils/` — Cross-cutting Helpers

```
utils/
├── auth.py / auth_utils.py         # JWT creation, validation
├── config.py / config_utils.py     # HOCON config loading
├── errors.py / errors_utils.py     # HTTP error factories
├── http.py / http_client_utils.py  # Outbound HTTP helpers
├── logging.py / logging_utils.py   # Structured logging setup
├── pagination.py                   # Cursor/offset pagination helpers
├── parsing_utils.py                # Generic string/type parsing
├── sql_utils.py                    # SQL fragment helpers
├── type_coerce.py                  # Type coercion utilities
├── uuid.py / uuid_utils.py         # Deterministic UUID generation
└── gclql_query_parser_utils.py     # GCLQL tokenizer/parser
```

> Note: The `*_utils.py` naming is the original convention from the template. The cleaner names (`auth.py`, `config.py`, etc.) are part of the ongoing refactor. Both exist during the transition; the `*_utils.py` variants will be removed once all imports are updated.