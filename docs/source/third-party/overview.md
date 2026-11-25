# Third-Party Integration Overview

UMB exposes a versioned HTTP/JSON API designed for external analysis frameworks (such as **FCCAnalyses**), Jupyter notebooks, workflow managers (DIRAC, Rucio, Snakemake), and custom web or CLI clients.

## Base URL & API Lifecycle

All version 1 endpoints are mounted under `/api/v1`:

```text
https://<umb-host>/api/v1
```

Each API version is wrapped by the lifecycle-aware `Api` container (`app/api/dependencies.py`):

| Lifecycle State | Behavior | Headers / Status |
|---|---|---|
| `ACTIVE` | Normal routing | `200 OK` |
| `DEPRECATED` | Still serves traffic, emits RFC deprecation warnings | `Deprecation: true`, `Warning: 299 - "API v1 is deprecated"` |
| `SUNSET` | Hard rejected | `410 Gone` with JSON pointing to `current_version` and `docs` |

Every response also includes observability headers injected by `TimingMiddleware`:

- `X-Process-Time`: server-side latency in milliseconds (e.g. `4.18ms`)
- `X-Request-Id`: echoed from client's `X-Request-Id` header or auto-generated UUIDv4 for log correlation

## Authentication & Token Refresh

Authentication is controlled server-side via `METADATA_BROWSER_AUTH_ENABLED`:

- **Public mode (`false`)**: Requests without an `Authorization` header resolve to an anonymous principal (`username: "anonymous"`, `roles: ["reader", "writer"]`, `authenticated: false`).
- **Protected mode (`true`)**: Protected routes (such as `/collections/*` and `/jobs/*`) require `Authorization: Bearer <accessToken>` and return `401 Unauthorized` otherwise.

### Obtaining & Refreshing Tokens

1. **Login** via `POST /api/v1/auth/login` with `{"username": "...", "password": "..."}` to receive:
   ```json
   {
     "accessToken": "<hs256-jwt>",
     "refreshToken": "<hs256-refresh-jwt>",
     "tokenType": "bearer",
     "expiresIn": 3600
   }
   ```
2. **Attach** `Authorization: Bearer <accessToken>` on subsequent calls.
3. **Refresh** on `401` (or proactively before `expiresIn` elapses) by posting `{"refreshToken": "..."}` to `POST /api/v1/auth/refresh`.
4. **Verify** current status via `GET /api/v1/auth/me`.

## Response & Validation Envelope

All `/api/v1/entity/*` endpoints return a structured `Response` envelope:

```json
{
  "apiInformation": {
    "version": "v1",
    "timestamp": "2026-11-24T17:00:00Z",
    "requestId": "c1f8a..."
  },
  "validationResult": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "status": "ok",
  "entities": [],
  "returned": 0,
  "nextCursor": null,
  "hasMore": false
}
```

- Always inspect `validationResult.valid` (and `status === "error"`) on `/entity/*` calls: semantic errors (such as combining `id` with `where`, or requesting `versions` without `id`) return HTTP `200` with `validationResult.valid = false` and descriptive `validationResult.errors`.
- Non-blocking advice (such as `page` without `sort`, or `contains`-only full scans) is returned in `validationResult.warnings`.
- Malformed JSON or schema type errors return standard FastAPI HTTP `422 Unprocessable Entity`.

## Integration Patterns & Recommendations

- **Use `take` on large catalogs** to keep payloads small when only a few metadata paths (e.g., `name`, `ecm`, `cross_section_pb`) are needed.
- **Paginate with `page` + `sort`** rather than fetching unbounded lists: pass `nextCursor` back as `page.cursor` until `hasMore` is `false`.
- **Use `/api/v1/jobs/` for heavy exports or histograms**: submit the job, store the returned `id`, and poll `GET /api/v1/jobs/{id}` until `status` is `"done"` or `"failed"`, then fetch `GET /api/v1/jobs/{id}/result`.
- **Forward `X-Request-Id`** from your pipeline or CI job ID so server logs in `RequestLoggingMiddleware` map 1-to-1 to your batch run.
