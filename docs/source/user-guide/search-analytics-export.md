# Navigation, Search, Analytics, Export, Collections & Jobs

Beyond the core `/api/v1/entity/` DSL, UMB provides domain-specific endpoints for discovery, statistical analysis, scientific format export, curated collections, and durable background jobs.

## Hierarchical Navigation & Field Discovery

- `GET /api/v1/navigation/accelerators`, `/campaigns`, `/detectors`, `/stages` return distinct values and entry counts.
- `GET /api/v1/navigation/fields` lists every metadata key, inferred type, and source recorded in `field_registry`.
- `GET /api/v1/navigation/values/{field_name}` returns distinct facet counts for any custom metadata key.

## Search

- **Full-text** (`GET /api/v1/search/?q=Whizard&limit=25`): Combines PostgreSQL `pg_trgm` similarity with token scoring (keeping underscored physics identifiers like `ee_ZH` intact) and returns `matchedFields`.
- **Similar datasets** (`GET /api/v1/search/similar/{entity_id}`): Ranks datasets of the same `entry_type` by weighted similarity across `process`, `ecm` proximity, `generator`, `campaign`, `detector`, and leaf Jaccard overlap.
- **Autocomplete** (`GET /api/v1/search/suggest?field=campaign&prefix=win`): Returns prefix-prioritized suggestions.

## Analytics

- **Histogram** (`POST /api/v1/analytics/histogram`): Uniform-width numeric binning over any nested metadata path.
- **Summary** (`POST /api/v1/analytics/summary`): Group-by counts plus optional `sum`, `mean`, `min`, and `max` on a numeric metric path.
- **Compare** (`POST /api/v1/analytics/compare`): Computes `meanA`, `meanB`, `delta` (`B - A`), and `ratio` (`B / A`) between two arbitrary `EntityRequestModel` cohorts.
- **Phase-Space Coverage** (`GET /api/v1/analytics/coverage?row_field=process&col_field=ecm`): Builds a 2D `(row, col, count)` coverage matrix.

## Multi-Format Scientific Export

`POST /api/v1/export/{format}` accepts any `EntityRequestModel` (including `take`, `where`, `sort`, `get`) and returns a downloadable attachment (`Content-Disposition: attachment; filename="umb_export.<ext>"`):

| Format | Endpoint | Output Style |
|---|---|---|
| CSV | `/api/v1/export/csv` | Flattened dot-path columns |
| JSON | `/api/v1/export/json` | Pretty-printed JSON array |
| YAML | `/api/v1/export/yaml` | FCCAnalyses-compatible `processList:` mapping |
| TOML | `/api/v1/export/toml` | `[[entries]]` array of tables |
| Python | `/api/v1/export/python` | Notebook-ready `processList = { ... }` literal |

## Collections & Durable Async Jobs

- **Collections** (`/api/v1/collections/`): Save private or public named sets of dataset UUIDs and manage membership via `POST /api/v1/collections/{id}/events` (`{ "add": [...], "remove": [...] }`).
- **Async Jobs** (`/api/v1/jobs/`): Offload large exports (`export`) or heavy aggregations (`analytics_histogram`, `analytics_summary`) to the Redis-backed `JobWorker`. Submitted jobs persist in PostgreSQL + Redis AOF and survive API or worker restarts.
