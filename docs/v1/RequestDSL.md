Here's the complete specification:

---

# UMB Request Model
UMB Request Model is a JSON-based domain specific language that enables users, software and third-party implementations to have readability, accessibility and fluency in their requests.
The model at core is based on three main modules, which are then abstracted by a single request model layer. This is done to make sure that the client can retrieve exactly the data they need and have their conditional scenarios implemented right inside the request, instead of requesting a bulk of metadata and filtering it on the client side.

## Core Structure
The fundamental units in every request are:
1. Fields that the client needs present in or absent from the response;
2. Filters that constrain the metadata based on the values of its keys;
3. Options that operate on the resulting collection before it is returned.

Each of these units can be filled with different clauses, described one by one below.

---

## Fields
A general model of metadata can be regarded as a map of keys and values:
```text
Metadata : Key (String) -> Value (Any Type)
```
Field clauses operate on the keys of metadata — either requiring their presence, requiring their absence, or selecting which keys to include in the response payload.

### `contains`
Requires that returned entries contain all specified keys, regardless of their values.
```json
{
    "contains": ["ecm", "event_number"]
}
```
> Give me entries that have both `ecm` and `event_number` defined.

### `without`
Requires that returned entries do not contain any of the specified keys.
```json
{
    "without": ["simulation", "test"]
}
```
> Give me entries that have neither `simulation` nor `test` defined.

### `take`
Selects which keys to include in the response payload. Entries are still fetched in full from the database; only the specified keys are returned to the client. Useful for reducing response size when only a subset of metadata is needed.
```json
{
    "take": ["ecm", "campaign", "source"]
}
```
> Give me only the `ecm`, `campaign` and `source` fields of each matched entry.

---

## Filters
Filters constrain the returned entries based on the values of their metadata keys. Unlike fields, which operate on key presence or absence, filters evaluate the value stored under a key against a condition.

A filter is expressed as a key paired with a condition string inside the `where` clause:
```text
"key": "<operator><value>"
```

### Operators
| Operator | Meaning |
|---|---|
| `=` | Equal |
| `!=` | Not equal |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |
| `~` | Fuzzy match |
| `:in[...]` | Value is one of a set |

### `where`
The primary filter clause. Each key in the `where` object is a metadata key, and its value is a condition string.
```json
{
    "where": {
        "ecm": ">10",
        "source": "=DIRAC",
        "campaign": "~LHC_2024"
    }
}
```
> Give me entries where `ecm` is greater than 10, `source` is exactly DIRAC, and `campaign` fuzzy-matches LHC_2024.

Multiple conditions on the same key are expressed in a single string:
```json
{
    "where": {
        "ecm": ">10 and <100 or None"
    }
}
```
> Give me entries where `ecm` is between 10 and 100 or No key/value for ecm field.

A set condition uses `:in[...]` syntax:
```json
{
    "where": {
        "source": ":in[DIRAC, RUCIO, CMS]"
    }
}
```
> Give me entries where `source` is one of DIRAC, RUCIO or CMS.

The wildcard key `*` applies a condition across all metadata keys:
```json
{
    "where": {
        "*": ">=302"
    }
}
```
> Give me entries where any metadata value is greater than or equal to 302.

### `search`
Full-text fuzzy search across all metadata values at once, without specifying a key.
```json
{
    "search": "proton collision 3.5"
}
```
> Give me entries whose metadata contains values resembling `proton collision 3.5`.

---

## Options
Options operate on the collection of matched entries after the database query is resolved. They do not affect which entries are matched — only how the resulting collection is shaped, ordered and returned.

### `get`
Controls how many entries are returned and the selection strategy.

| Sub-key | Meaning |
|---|---|
| `first` | First N entries |
| `last` | Last N entries |
| `random` | N entries sampled randomly |
| `uniform` | N entries sampled uniformly across the result space |

```json
{
    "get": {"random": 100}
}
```
> From the matched entries, return 100 sampled at random.

### `sort`
Sorts the matched entries by a metadata key before returning.

| Sub-key | Meaning |
|---|---|
| `by` | The key to sort by |
| `order` | `asc` or `desc` |

```json
{
    "sort": {"by": "ecm", "order": "desc"}
}
```
`sort` and `get` compose — sorting is applied before selection, so `random` draws from a sorted pool if both are present.

### `page`
Paginates the response using cursor-based pagination.

| Sub-key | Meaning |
|---|---|
| `size` | Number of entries per page |
| `cursor` | ID of the last seen entry from the previous page |

```json
{
    "page": {"size": 10, "cursor": "uuid-here"}
}
```

### `aggregate`
Computes a scalar value over a metadata key across all matched entries instead of returning the entries themselves.

| Sub-key | Meaning |
|---|---|
| `by` | The key to aggregate over |
| `fn` | `count`, `avg`, `min`, `max`, `sum` |

```json
{
    "aggregate": {"by": "ecm", "fn": "avg"}
}
```
> Return the average value of `ecm` across all matched entries.

### `distinct`
Returns all unique values of a single metadata key across matched entries instead of returning the entries themselves.
```json
{
    "distinct": "source"
}
```
> Return all unique values of `source` across matched entries.

### `count`
Returns only the count of matched entries, not the entries themselves.
```json
{
    "count": true
}
```

---

## Entry Selection
Beyond fields and filters, the following top-level keys target specific entries or versions directly.

### `entry_type`
Constrains the query to one or more entry types.
```json
{
    "entry_type": "collision"
}
```
```json
{
    "entry_type": ["collision", "beam_config"]
}
```

### `id`
Targets a specific entry by its UUID.
```json
{
    "id": "uuid-here"
}
```

### `version`
Targets a specific version of an entry. Bypasses the default `is_current` filter.
```json
{
    "version": 3
}
```

### `versions`
Returns the last N versions of a specific entry.
```json
{
    "id": "uuid-here",
    "versions": {"last": 5}
}
```

### `snapshot`
Returns entries as they existed at a specific point in time, using version history.
```json
{
    "snapshot": "2024-06-01T00:00:00Z"
}
```

---

## Full Example
```json
{
    "entry_type": "collision",
    "where": {
        "ecm": ">10 <100",
        "source": ":in[DIRAC, RUCIO]"
    },
    "contains": ["campaign", "event_number"],
    "without": ["simulation"],
    "take": ["ecm", "campaign", "source"],
    "get": {"random": 100},
    "sort": {"by": "ecm", "order": "desc"},
    "page": {"size": 10, "cursor": "uuid-here"}
}
```
> From collision entries where `ecm` is between 10 and 100, source is DIRAC or RUCIO, and both `campaign` and `event_number` are present, excluding any with `simulation` defined — return 100 random entries sorted by `ecm` descending, showing only `ecm`, `campaign` and `source`, paginated at 10 per page.

