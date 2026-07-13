# UMB Request Model

The UMB Request Model is a JSON-based domain-specific language that enables users, software, and third-party implementations to express rich metadata queries in a readable, accessible, and composable manner.

The model is built around three core concepts:

1. **Fields**, which describe the metadata that must exist, must not exist, or should be returned.
2. **Filters**, which constrain entries based on metadata values.
3. **Options**, which shape the resulting collection after matching.

Unlike traditional query languages that treat metadata as a flat map, the UMB Request Model assumes metadata is a hierarchical tree. Consequently, every metadata-oriented clause mirrors the structure of the metadata itself.

---

# Metadata Model

Metadata is regarded as a hierarchical structure of nested objects and values.

```text
Metadata ::= Value
           | Object<String, Metadata>
```

Metadata is therefore identified by **metadata paths**.

Examples:

```text
ecm
parent.ecm
parent.generator.version
```

Rather than writing paths explicitly, the request model represents them naturally through nested JSON objects. Every nested object corresponds to another level of metadata.

For example, the metadata

```json
{
    "ecm": 13.6,
    "parent": {
        "generator": {
            "name": "Pythia",
            "version": "8.3"
        }
    }
}
```

is addressed in the request language using the same hierarchy.

---

# Core Structure

Every request consists of a combination of:

* Entry selection
* Fields
* Filters
* Options

Each section is independent and composable.

---

# Fields

Field clauses operate on the presence or absence of metadata paths and determine which metadata should be returned.

---

## `contains`

Requires that returned entries contain every specified metadata path.

```json
{
    "contains": {
        "ecm": {},
        "parent": {
            "generator": {
                "version": {}
            }
        }
    }
}
```

> Return entries containing both `ecm` and `parent.generator.version`.

---

## `without`

Requires that returned entries do not contain any of the specified metadata paths.

```json
{
    "without": {
        "simulation": {},
        "parent": {
            "private": {}
        }
    }
}
```

> Return entries that do not contain `simulation` nor `parent.private`.

---

## `take`

Selects which metadata should be included in the response payload.

Entries are still retrieved in full from the database. The `take` clause only affects the metadata returned to the client.

```json
{
    "take": {
        "ecm": {},
        "campaign": {},
        "parent": {
            "generator": {
                "name": {}
            }
        }
    }
}
```

Returned metadata preserves the requested hierarchy.

Example response:

```json
{
    "ecm": 13.6,
    "campaign": "Run3",
    "parent": {
        "generator": {
            "name": "Pythia"
        }
    }
}
```

---

# Filters

Filters constrain returned entries according to the values stored at metadata paths.

A filter is expressed as a metadata tree whose leaves are condition strings.

```text
"path": "<operator><value>"
```

---

## Operators

| Operator   | Meaning                |
| ---------- | ---------------------- |
| `=`        | Equal                  |
| `!=`       | Not equal              |
| `>`        | Greater than           |
| `<`        | Less than              |
| `>=`       | Greater than or equal  |
| `<=`       | Less than or equal     |
| `~`        | Fuzzy match            |
| `:in[...]` | Value belongs to a set |

---

## `where`

The primary filtering clause.

Each nested object represents another level in the metadata hierarchy. Condition strings always appear at leaf nodes.

```json
{
    "where": {
        "ecm": ">10",
        "source": "=DIRAC",
        "parent": {
            "generator": {
                "version": "=8.3"
            }
        }
    }
}
```

> Return entries where `ecm` is greater than 10, `source` equals DIRAC, and `parent.generator.version` equals 8.3.

---

Multiple conditions can be combined in a single expression.

```json
{
    "where": {
        "ecm": ">10 and <100 or None"
    }
}
```

> Return entries where `ecm` is between 10 and 100, or where the field is absent.

---

A set condition uses `:in[...]`.

```json
{
    "where": {
        "source": ":in[DIRAC, RUCIO, CMS]"
    }
}
```

> Return entries whose source is one of DIRAC, RUCIO, or CMS.

---

The wildcard `*` applies a condition across all metadata values.

```json
{
    "where": {
        "*": ">=302"
    }
}
```

> Return entries where any metadata value is greater than or equal to 302.

---

## `search`

Performs a fuzzy full-text search across all metadata values.

```json
{
    "search": "proton collision 13.6"
}
```

> Return entries whose metadata resembles "proton collision 13.6".

---

# Options

Options operate on the matched collection after filtering.

They never affect which entries match.

---

## `get`

Controls how many entries are returned and how they are selected.

| Sub-key   | Meaning                                |
| --------- | -------------------------------------- |
| `first`   | First N entries                        |
| `last`    | Last N entries                         |
| `random`  | Random sample of N entries             |
| `uniform` | Uniform sample across the result space |

```json
{
    "get": {
        "random": 100
    }
}
```

---

## `sort`

Sorts matched entries by a metadata path.

```json
{
    "sort": {
        "by": {
            "parent": {
                "ecm": {}
            }
        },
        "order": "desc"
    }
}
```

| Sub-key | Meaning         |
| ------- | --------------- |
| `by`    | Metadata path   |
| `order` | `asc` or `desc` |

Sorting is performed before `get`.

---

## `page`

Cursor-based pagination.

| Sub-key  | Meaning          |
| -------- | ---------------- |
| `size`   | Entries per page |
| `cursor` | Last seen entry  |

```json
{
    "page": {
        "size": 10,
        "cursor": "uuid-here"
    }
}
```

---

## `aggregate`

Computes an aggregate over a metadata path.

| Sub-key | Meaning                             |
| ------- | ----------------------------------- |
| `by`    | Metadata path                       |
| `fn`    | `count`, `avg`, `min`, `max`, `sum` |

```json
{
    "aggregate": {
        "by": {
            "parent": {
                "ecm": {}
            }
        },
        "fn": "avg"
    }
}
```

> Return the average value of `parent.ecm`.

---

## `distinct`

Returns every unique value for a metadata path.

```json
{
    "distinct": {
        "parent": {
            "generator": {
                "name": {}
            }
        }
    }
}
```

---

## `count`

Returns only the number of matched entries.

```json
{
    "count": true
}
```

---

# Entry Selection

These clauses target specific entries independently of metadata filtering.

---

## `entry_type`

Restricts the query to one or more entry types.

```json
{
    "entry_type": "collision"
}
```

```json
{
    "entry_type": [
        "collision",
        "beam_config"
    ]
}
```

---

## `id`

Targets a specific entry.

```json
{
    "id": "uuid-here"
}
```

---

## `version`

Targets a specific version of an entry.

```json
{
    "version": 3
}
```

This bypasses the default `is_current` filter.

---

## `versions`

Returns multiple versions of an entry.

```json
{
    "id": "uuid-here",
    "versions": {
        "last": 5
    }
}
```

---

## `snapshot`

Returns entries exactly as they existed at a given time.

```json
{
    "snapshot": "2024-06-01T00:00:00Z"
}
```

---

# Complete Example

```json
{
    "entry_type": "collision",

    "where": {
        "ecm": ">10 and <100",
        "source": ":in[DIRAC, RUCIO]",
        "parent": {
            "generator": {
                "version": "=8.3"
            }
        }
    },

    "contains": {
        "campaign": {},
        "event_number": {}
    },

    "without": {
        "simulation": {}
    },

    "take": {
        "ecm": {},
        "campaign": {},
        "source": {},
        "parent": {
            "generator": {
                "name": {}
            }
        }
    },

    "sort": {
        "by": {
            "ecm": {}
        },
        "order": "desc"
    },

    "get": {
        "random": 100
    },

    "page": {
        "size": 10,
        "cursor": "uuid-here"
    }
}
```

> From collision entries where `ecm` is between 10 and 100, `source` is either DIRAC or RUCIO, and `parent.generator.version` is 8.3; require the presence of `campaign` and `event_number`, exclude entries containing `simulation`, return only the selected metadata, sort by `ecm` descending, randomly sample 100 entries, and paginate the results in pages of 10.
