# Complete API v1 Reference

Interactive OpenAPI/Swagger documentation is served live at `/api/v1/docs` and `/api/v1/openapi.json`. The table below summarizes all 38 routes across the 8 domains plus system health.

## System Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/check/` | Health and API version check |

## Entities (`/api/v1/entity`)

| Method | Path | Body / Query | Description |
|---|---|---|---|
| `POST` | `/api/v1/entity/` | `EntityRequestModel` | Full DSL dispatcher (query, stat, versions, pagination) |
| `POST` | `/api/v1/entity/query` | `EntityRequestModel` | Filtered/sorted entity query |
| `POST` | `/api/v1/entity/search` | `EntityRequestModel` (requires `search`) | Trigram fuzzy search over JSONB values |
| `POST` | `/api/v1/entity/stat` | `EntityRequestModel` (requires `aggregate`, `distinct`, or `count`) | Aggregations, distinct values, or counts |
| `POST` | `/api/v1/entity/get` | `EntityRequestModel` | Direct lookup by `id`, `version`, `versions`, or `snapshot` |
| `GET` | `/api/v1/entity/rand` | `?n=1&entry_type=...` (`1 <= n <= 100`) | Random sample of current entries |

## Navigation (`/api/v1/navigation`)

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/api/v1/navigation/accelerators` | `?entry_type=` | Distinct `accelerator` facet values & counts |
| `GET` | `/api/v1/navigation/campaigns` | `?entry_type=` | Distinct `campaign` facet values & counts |
| `GET` | `/api/v1/navigation/detectors` | `?entry_type=` | Distinct `detector` facet values & counts |
| `GET` | `/api/v1/navigation/stages` | `?entry_type=` | Distinct `stage` facet values & counts |
| `GET` | `/api/v1/navigation/fields` | `?entry_type=` | All discovered keys/types from `field_registry` |
| `GET` | `/api/v1/navigation/values/{field_name}` | `?entry_type=` | Distinct values & counts for any metadata key |

## Search (`/api/v1/search`)

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/api/v1/search/` | `?q=...&entry_type=&limit=25` | Ranked full-text search with `matchedFields` |
| `GET` | `/api/v1/search/similar/{entity_id}` | `?limit=10` | Physics-weighted similar datasets |
| `GET` | `/api/v1/search/suggest` | `?field=...&prefix=&entry_type=&limit=15` | Prefix-first autocomplete suggestions |

## Analytics (`/api/v1/analytics`)

| Method | Path | Payload / Query | Description |
|---|---|---|---|
| `POST` | `/api/v1/analytics/histogram` | `{ field, bins?, entry_type?, where? }` | Uniform-width numeric histogram |
| `POST` | `/api/v1/analytics/summary` | `{ groupBy, metric?, entry_type?, where? }` | Group-by counts + optional `sum`/`mean`/`min`/`max` |
| `POST` | `/api/v1/analytics/compare` | `{ groupA, groupB, metrics }` | Cohort comparison (`meanA`, `meanB`, `delta`, `ratio`) |
| `GET` | `/api/v1/analytics/coverage` | `?row_field=process&col_field=ecm&entry_type=` | 2D phase-space coverage matrix |

## Export (`/api/v1/export`)

All export routes accept `EntityRequestModel` and return an attachment download:

| Method | Path | `Content-Type` | Filename |
|---|---|---|---|
| `POST` | `/api/v1/export/csv` | `text/csv; charset=utf-8` | `umb_export.csv` |
| `POST` | `/api/v1/export/json` | `application/json; charset=utf-8` | `umb_export.json` |
| `POST` | `/api/v1/export/yaml` | `application/x-yaml; charset=utf-8` | `umb_export.yaml` |
| `POST` | `/api/v1/export/toml` | `application/toml; charset=utf-8` | `umb_export.toml` |
| `POST` | `/api/v1/export/python` | `text/x-python; charset=utf-8` | `umb_export.py` |

## Authentication (`/api/v1/auth`)

| Method | Path | Body / Headers | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | `{ username, password }` | Issue HS256 `accessToken` + `refreshToken` |
| `POST` | `/api/v1/auth/refresh` | `{ refreshToken }` | Mint fresh token pair |
| `GET` | `/api/v1/auth/me` | `Authorization: Bearer ...` (optional if auth disabled) | Current auth mode & principal |

## Collections (`/api/v1/collections`)

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/v1/collections/` | — | List user's collections + public collections |
| `POST` | `/api/v1/collections/` | `{ name, description?, isPublic? }` | Create collection |
| `GET` | `/api/v1/collections/{collection_id}` | — | Collection metadata + `entryIds` |
| `PUT` | `/api/v1/collections/{collection_id}` | `{ name?, description?, isPublic? }` | Update collection (owner/admin only) |
| `DELETE` | `/api/v1/collections/{collection_id}` | — | Delete collection (owner/admin only) |
| `POST` | `/api/v1/collections/{collection_id}/events` | `{ add: [...], remove: [...] }` | Modify collection membership |

## Async Jobs (`/api/v1/jobs`)

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/jobs/` | `{ taskType, payload }` | Persist job (`pending`) & enqueue in Redis |
| `GET` | `/api/v1/jobs/` | — | List caller's submitted jobs |
| `GET` | `/api/v1/jobs/{job_id}` | — | Poll job status (`pending`/`running`/`done`/`failed`) |
| `GET` | `/api/v1/jobs/{job_id}/result` | — | Fetch completed JSONB `result` or `error` |

Supported `taskType` values: `"export"`, `"analytics_histogram"`, `"analytics_summary"`.
