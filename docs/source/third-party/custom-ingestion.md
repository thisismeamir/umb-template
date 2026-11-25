# Custom Metadata Ingestion (External Producers)

External pipelines (e.g., DIRAC production scripts, EOS sync cron jobs, or Monte Carlo campaign generators) can feed metadata into UMB without calling any write HTTP endpoint by dropping structured JSON files into the watched storage directory.

## File Naming Contract

`FileWatcher` (`backend/app/workers/FileWatcher.py`) enforces a strict double-underscore filename convention:

```text
<entry_type>__<source>__<created_by>.json
```

Regex enforced by `FileWatcher.FILENAME_PATTERN`:

```text
^(?P<entry_type>[^_]+)__(?P<source>[^_]+)__(?P<created_by>[^_]+)\.json$
```

- `entry_type`: Logical dataset category (e.g. `collision`, `simulation`, `detectorConfig`). **Do not include underscores** inside individual segments.
- `source`: Provenance system (e.g. `DIRAC`, `RUCIO`, `EOS`, `TOOL`).
- `created_by`: Producer username or service account (e.g. `amir`, `fccbot`).

Files not matching this pattern are skipped and logged.

## JSON Payload Format

Each file must contain a **top-level JSON array** of objects. Objects may be arbitrarily nested:

```json
[
  {
    "name": "wzp6_ee_ZH_ecm240",
    "process": "ee_ZH",
    "ecm": 240.0,
    "campaign": "winter2023",
    "detector": "IDEA",
    "generator": {
      "name": "Whizard",
      "version": "3.1.2"
    },
    "cross_section_pb": 0.201
  }
]
```

## Reserved System Keys

Before inserting into `entries.metadata`, `FileWatcher._cleanMetadata()` automatically strips these legacy/system keys to avoid collisions with SQL columns:

- `uuid`
- `created_at`
- `updated_at`
- `last_edited_at`
- `entity_id`

## Atomic Drop Pattern & Lifecycle

1. **Write to a temporary file outside the watched extension** (e.g., `collision__DIRAC__fccbot.json.tmp`) and atomically `mv` it to `.json` so `FileWatcher` never reads a half-written file.
2. `FileWatcher` inserts all entries inside a single PostgreSQL transaction, registers each top-level key and Python value type in `field_registry` (`ON CONFLICT DO NOTHING`), and moves the file to `<fileWatcherRoot>/processed/`.
3. On backend restart, `FileWatcher._scan()` processes **only** pending `*.json` files in `<fileWatcherRoot>` and never re-ingests files already moved into `processed/`.

## Automatic Field Discovery

As soon as a batch is ingested:

- All newly discovered keys become visible via `GET /api/v1/navigation/fields`.
- Any scalar key is immediately queryable via `GET /api/v1/navigation/values/{key}`, `GET /api/v1/search/suggest?field={key}`, and the Request DSL `where` / `contains` / `without` / `take` / `sort` / `aggregate` clauses.
