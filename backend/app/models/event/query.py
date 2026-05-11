# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN — Apache License 2.0
#  Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------
"""
Structured query model for FCC Physics Events.

Design:
  - Fields   : exact-match constraints on FK-backed columns (always DB-resolvable)
  - Filters  : range / set operators on numeric/string metadata (may be JSON or derived)
  - Options  : result-set controls (limit, offset, sort)

The split matters because Fields translate directly to SQL WHERE clauses, while
Filters may require post-processing when the target field lives in a JSON column
or is derived from the dataset name (e.g. ecm is embedded as "ecm365" in `name`).
"""
from __future__ import annotations

import json
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Operator vocabulary
# ---------------------------------------------------------------------------

class NumericOp(str, Enum):
    gt  = "gt"   # >
    gte = "gte"  # >=
    lt  = "lt"   # <
    lte = "lte"  # <=
    eq  = "eq"   # ==
    neq = "neq"  # !=


class NumericFilter(BaseModel):
    """A single comparison on a numeric metadata field."""
    op: NumericOp
    value: float


class RangeFilter(BaseModel):
    """Inclusive range shorthand — equivalent to gte + lte."""
    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> "RangeFilter":
        if self.min is None and self.max is None:
            raise ValueError("RangeFilter requires at least one of min or max")
        return self


# A filter value is either a single comparison or a range.
FilterValue = NumericFilter | RangeFilter | list[Any]


# ---------------------------------------------------------------------------
# The three query layers
# ---------------------------------------------------------------------------

class EventFields(BaseModel):
    """
    Exact-match constraints on FK-backed relational columns.
    All values are resolved by the engine to integer IDs before the SQL query.

    Unset fields are ignored (no constraint applied).
    """
    accelerator : str | None = Field(None, examples=["fcc-ee"])
    stage       : str | None = Field(None, examples=["rec", "gen"])
    campaign    : str | None = Field(None, examples=["winter2023"])
    detector    : str | None = Field(None, examples=["IDEA", "CLD"])
    file_type   : str | None = Field(None, examples=["edm4hep-root"])
    status      : str | None = Field(None, examples=["done", "running", "failed"])


class EventFilters(BaseModel):
    """
    Numeric / set constraints on metadata fields.

    These fields may live in a JSON column or be derived from the dataset name,
    so they are applied as a post-SQL Python filter unless the repository has
    a dedicated materialized column for them.

    All fields are optional; unset means no constraint.
    """
    # Physics parameters
    ecm             : RangeFilter | None = Field(None, description="Centre-of-mass energy [GeV]")
    cross_section   : RangeFilter | None = Field(None, description="Cross-section [pb]")
    n_events        : RangeFilter | None = Field(None, description="Number of generated events")
    k_factor        : RangeFilter | None = Field(None, description="K-factor (NLO/LO ratio)")
    matching_eff    : RangeFilter | None = Field(None, description="Matching efficiency [0,1]")
    sum_of_weights  : RangeFilter | None = Field(None, description="Sum of generator weights")

    # File-level quality
    n_files_good    : RangeFilter | None = Field(None, description="Number of good files on EOS")
    n_files_bad     : RangeFilter | None = Field(None, description="Number of bad files (0 = clean dataset)")

    # Set membership
    gen_type        : list[str] | None   = Field(None, description="Generator type(s), e.g. ['wzp6','mg5']")
    rec_type        : list[str] | None   = Field(None, description="Reconstruction type(s)")
    sim_type        : list[str] | None   = Field(None, description="Simulation type(s)")


class EventOptions(BaseModel):
    """
    Result-set controls.  Kept intentionally minimal.
    """
    limit  : int  = Field(50,    ge=1, le=1000, description="Max results to return")
    offset : int  = Field(0,     ge=0,          description="Pagination offset")
    sort_by: str  = Field("name",               description="Column to sort by")
    order  : Literal["asc", "desc"] = Field("asc", description="Sort direction")

    # Projection: return only a subset of fields (None = return all)
    fields : list[str] | None = Field(None, description="Allowlist of response keys to include")


# ---------------------------------------------------------------------------
# Top-level query envelope
# ---------------------------------------------------------------------------

class EventQuery(BaseModel):
    """
    Full query envelope sent to the query engine.

    Example::

        {
          "fields":  {"accelerator": "fcc-ee", "detector": "IDEA"},
          "filters": {"ecm": {"min": 160, "max": 240}, "n_files_bad": {"max": 0}},
          "options": {"limit": 10, "sort_by": "cross_section", "order": "desc"}
        }
    """
    fields  : EventFields  = Field(default_factory=EventFields)
    filters : EventFilters = Field(default_factory=EventFilters)
    options : EventOptions = Field(default_factory=EventOptions)

    @staticmethod
    def from_string(query: str) -> EventQuery:
        return EventQuery(**json.loads(query))