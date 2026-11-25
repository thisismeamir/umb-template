# Request DSL Guide

The UMB Request DSL is a JSON query language posted to `/api/v1/entity/` (and specialized routes `/entity/query`, `/entity/search`, `/entity/stat`, `/entity/get`). Every metadata clause mirrors the nested tree structure of the stored JSONB documents.

## Request Sections

A request combines any subset of four sections:

1. **Entry Selection**: `entry_type`, `id`, `version`, `versions`, `snapshot`
2. **Fields**: `contains`, `without`, `take`
3. **Filters**: `where`, `search`
4. **Options**: `sort`, `get`, `page`, `aggregate`, `distinct`, `count`

## Entry Selection

| Clause | Type | Behavior |
|---|---|---|
| `entry_type` | `string \| string[]` | Restricts to one or more `entry_type` values. |
| `id` | `string (UUID)` | Targets a single entry; mutually exclusive with `entry_type`, `where`, `contains`, `without`, `search`. |
| `version` | `int` | Fetches a specific version (bypasses `is_current = TRUE`). Mutually exclusive with `versions`. |
| `versions` | `object` | Returns version history (`last`, `first`, `by`, `type`, `before`, `after`). Requires `id`. |
| `snapshot` | `ISO-8601 string` | Returns entries created at or before the given timestamp. |

## Field Clauses

- **`contains`**: Requires every leaf path (`{}`) to exist and be non-null.
- **`without`**: Excludes entries containing any of the listed leaf paths.
- **`take`**: Projects returned `metadata` to only the listed paths while preserving nested object hierarchy.

```json
{
  "contains": { "campaign": {}, "parent": { "generator": { "version": {} } } },
  "without": { "simulation": {} },
  "take": { "ecm": {}, "parent": { "generator": { "name": {} } } }
}
```

## Filter Clauses (`where` and `search`)

Leaf strings in `where` are compiled by the ANTLR4 grammar (`EntryFilter.g4`) into parameterized PostgreSQL JSONPath and `pg_trgm` SQL predicates.

### Supported Operators

| Operator | Example | Meaning |
|---|---|---|
| `=`, `!=` | `"=8.3"`, `"!=failed"` | Equality / inequality |
| `>`, `<`, `>=`, `<=` | `">10 and <100"` | Numeric or lexicographic comparison |
| `~` | `"~Pythia"` | Fuzzy trigram match (`similarity > 0.3`) |
| `:in [...]` | `":in [DIRAC, RUCIO]"` | Membership in set |
| `!in [...]` | `"!in [test, draft]"` | Exclusion from set |
| `and`, `or`, `( ... )` | `"(=240 or =365) and !=91"` | Boolean composition and grouping |
| `*` (wildcard key) | `{"*": ">=302"}` | Matches if **any** nested metadata value satisfies the condition |

### Full-Text `search`

```json
{
  "search": "proton collision 13.6"
}
```

Matches entries where any scalar JSONB leaf has trigram similarity `> 0.3`.

## Options (`sort`, `get`, `page`, `aggregate`, `distinct`, `count`)

- **`sort`**: `{ "by": { "ecm": {} }, "order": "desc" }` (single path; `asc` or `desc`, `NULLS LAST`).
- **`get`**: Post-fetch selection — specify at most one of `first`, `last`, `random`, or `uniform`.
- **`page`**: Cursor pagination `{ "size": 25, "cursor": "<last-uuid>" }`. Responses include `nextCursor` and `hasMore`.
- **`aggregate`**: `{ "by": { "ecm": {} }, "fn": "avg" }` (`count`, `sum`, `avg`, `min`, `max`).
- **`distinct`**: `{ "parent": { "generator": { "name": {} } } }` returns all unique non-null values.
- **`count`**: `true` returns the matched entry count.

## Complete Example

```json
{
  "entry_type": "collision",
  "where": {
    "ecm": ">100 and <=365",
    "source": ":in [DIRAC, RUCIO]"
  },
  "contains": { "campaign": {} },
  "without": { "private": {} },
  "take": { "name": {}, "ecm": {}, "campaign": {} },
  "sort": { "by": { "ecm": {} }, "order": "desc" },
  "page": { "size": 20 }
}
```
