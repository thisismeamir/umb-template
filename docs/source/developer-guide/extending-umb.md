# Extending UMB

UMB is designed so new domains, async worker tasks, export formats, and DSL clauses can be added without modifying unrelated layers.

## Adding a New Domain Module

Follow the established 5-layer pattern:

1. **Models** (`app/models/<domain>/`): Define Pydantic v2 request/response schemas (prefer `.model_dump()` over `.dict()`).
2. **Engine** (`app/engine/<domain>/`): Put pure, deterministic computation here with zero DB or HTTP imports so it can be unit-tested in isolation.
3. **Repository** (`app/repositories/<domain>/`): Write parameterized `asyncpg` queries (`$1`, `$2`, ...).
4. **Service** (`app/services/<domain>/`): Coordinate validation, engine calls, and repository queries.
5. **Router & Wiring** (`app/api/v1/<domain>/router.py`):
   - Add a module-level `async def _<domain>Service(...)` dependency callable in `app/api/dependencies.py` and expose it via `staticmethod` on `Provider`. (Keeping dependency callables at module level ensures FastAPI resolves `__globals__` cleanly under `from __future__ import annotations`.)
   - Mount the router in `ApiV1.__init__()` (`app/api/v1/router.py`).

## Registering a New Async Worker Task

1. Add a new enum member to `JobTaskType` in `app/models/jobs/JobModels.py`.
2. Implement an `async def _runMyTask(payload: dict[str, Any], repository: EntityRepository) -> Any` function in `app/workers/JobRegistry.py`.
3. Register it in `JobRegistry._handlers`.
4. Add unit coverage in `backend/test/EntryService/RedisJobWorkerTests.py`.

`JobService` and `JobWorker` automatically pick up the new task type with full Redis persistence and crash recovery.

## Adding a New Export Formatter

1. Add the format name to `ExportFormat` and its `(media_type, extension)` tuple to `EXPORT_MEDIA_TYPES` in `app/models/export/ExportModels.py`.
2. Implement the formatter method on `ExportFormatters` (`app/engine/export/ExportFormatters.py`) and dispatch it in `ExportFormatters.render()`.
3. Add a `POST /<format>` route in `app/api/v1/export/router.py` and mirror the format in `V1ExportFormat` (`frontend/types/api.ts`).

## Adding a New Request DSL Clause

1. Add the field and tree validation to `EntityRequestModel` (`app/models/request/EntityRequestModel.py`).
2. Add semantic conflict checks in `EntityRequestValidator` (`app/services/entity/EntityRequestValidatorService.py`).
3. Compile the SQL fragment in `SQLPlanner` using `?` placeholders (never `$N` manually — `_bindPlaceholders()` assigns `$1..$N` once at the top level) or add a post-fetch transform in `EntityEngine`.
4. Wire the response field in `EntityService.response()` and add tests in `EntityM1Tests.py`.
