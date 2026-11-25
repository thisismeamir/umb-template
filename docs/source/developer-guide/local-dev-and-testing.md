# Local Development & Testing

## Backend Setup (`uv`)

```bash
cd backend
uv sync
```

### Running Tests

The backend test suite lives under `backend/test/EntryService/`:

| Test File | Scope |
|---|---|
| `FilterDSLTests.py` | ANTLR4 filter grammar & `ExpressionHandler` |
| `EntityM1Tests.py` | `PathTreeToList`, models, `SQLPlanner`, `EntityEngine`, `EntityRequestValidator`, `EntityService`, `DatabaseInitializer`, `FileWatcher` |
| `EntityM2Tests.py` | `navigation`, `search`, `analytics`, and `export` engines & services |
| `EntityM3Tests.py` | `TimingMiddleware`, `RequestLoggingMiddleware`, `auth`, `collections`, and `jobs` |
| `ApiV1IntegrationTests.py` | End-to-end FastAPI `TestClient` HTTP tests across all 8 domains + middleware |
| `RedisJobWorkerTests.py` | `RedisJobQueue` claim/ack, `JobWorker` crash recovery, and failure handling |

Run the full suite:

```bash
cd backend
uv run pytest test/EntryService/
```

### Linting & Strict Type Checking

```bash
cd backend
uv run ruff check .
uv run mypy app
```

Generated ANTLR4 parser files in `app/engine/entry/grammar/` are excluded from `ruff` and `mypy` in `backend/pyproject.toml`.

### Regenerating the ANTLR4 Filter Grammar

If you edit `backend/app/engine/entry/grammar/EntryFilter.g4`, regenerate the Python lexer/parser/visitor with ANTLR 4.13+:

```bash
antlr4 -Dlanguage=Python3 -visitor -listener \
  backend/app/engine/entry/grammar/EntryFilter.g4
```

## Frontend Setup (`yarn`)

```bash
cd frontend
yarn install --frozen-lockfile
yarn lint
yarn type-check
yarn build
```

## Building the Documentation Locally

```bash
pip install -r docs/requirements.txt
make -C docs html
# Open docs/build/html/index.html
```

## Continuous Integration

`.github/workflows/ci.yml` runs two parallel jobs on pushes and pull requests:

- **`validate-frontend`**: `yarn install`, `yarn lint`, `yarn type-check`, `yarn build`, Docker image build.
- **`validate-backend`**: `uv sync`, `uv run ruff check .`, `uv run mypy app`, `uv run pytest test/EntryService/`, Docker image build.
