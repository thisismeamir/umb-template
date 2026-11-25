# CLI & Shell (`curl` / `jq`) Recipes

These copy-paste recipes are designed for CI scripts, batch submission wrappers, and quick terminal inspection. Set `UMB_API` once:

```bash
export UMB_API="http://localhost:8000/api/v1"
```

## 1. Authenticate & Export Bearer Token

```bash
export UMB_TOKEN=$(curl -sS -X POST "$UMB_API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "amir", "password": "secret"}' | jq -r '.accessToken')
```

Verify identity and auth mode:

```bash
curl -sS "$UMB_API/auth/me" -H "Authorization: Bearer $UMB_TOKEN" | jq
```

## 2. Query Entities with the Request DSL

```bash
curl -sS -X POST "$UMB_API/entity/query" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: batch-run-042" \
  -d '{
    "entry_type": "collision",
    "where": { "ecm": ">=240 and <=365" },
    "without": { "private": {} },
    "take": { "name": {}, "ecm": {}, "campaign": {} },
    "sort": { "by": { "ecm": {} }, "order": "desc" },
    "page": { "size": 10 }
  }' | jq
```

## 3. Discover Available Fields & Facets

```bash
# List all discovered metadata fields from field_registry
curl -sS "$UMB_API/navigation/fields" | jq '.fields[] | "\(.entryType).\(.key) (\(.valueType))"'

# Facet counts by campaign
curl -sS "$UMB_API/navigation/campaigns" | jq
```

## 4. Export Directly to Disk (YAML, CSV, Python)

```bash
curl -sS -X POST "$UMB_API/export/yaml" \
  -H "Content-Type: application/json" \
  -d '{"entry_type": "collision", "where": {"campaign": "=winter2023"}}' \
  -o processList.yaml
```

## 5. Submit & Poll a Durable Async Job

```bash
JOB_ID=$(curl -sS -X POST "$UMB_API/jobs/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UMB_TOKEN" \
  -d '{
    "taskType": "analytics_histogram",
    "payload": { "field": { "ecm": {} }, "bins": 10 }
  }' | jq -r '.id')

echo "Submitted job: $JOB_ID"

while true; do
  STATUS=$(curl -sS "$UMB_API/jobs/$JOB_ID" \
    -H "Authorization: Bearer $UMB_TOKEN" | jq -r '.status')
  echo "Status: $STATUS"
  [[ "$STATUS" == "done" || "$STATUS" == "failed" ]] && break
  sleep 1
done

curl -sS "$UMB_API/jobs/$JOB_ID/result" \
  -H "Authorization: Bearer $UMB_TOKEN" | jq
```
