from typing import Any, Dict, List, Tuple

from app.models.event.query import (
    EventQuery,
    NumericFilter,
    RangeFilter,
)
from app.engine.query.plan import EventRepositoryRequestPlan


FIELD_COLUMN_MAP = {
    "accelerator": "accelerator_name",
    "stage": "stage_name",
    "campaign": "campaign_name",
    "detector": "detector_name",
    "file_type": "file_type_name",
    "status": "status",
}

FILTER_COLUMN_MAP = {
    "cross_section": "cross_section",
    "n_events": "n_events",
    "k_factor": "k_factor",
    "matching_eff": "matching_eff",
    "sum_of_weights": "sum_of_weights",
    "n_files_good": "n_files_good",
    "n_files_bad": "n_files_bad",
}


class EventQueryEngine:

    @staticmethod
    def compile(query: EventQuery) -> EventRepositoryRequestPlan:
        clauses: List[str] = []
        params: Dict[str, Any] = {}

        # -----------------------------------------------------------------
        # 1. FIELDS (exact match)
        # -----------------------------------------------------------------
        field_clauses, field_params = EventQueryEngine._compile_fields(query)
        clauses.extend(field_clauses)
        params.update(field_params)

        # -----------------------------------------------------------------
        # 2. FILTERS (range / operators)
        # -----------------------------------------------------------------
        filter_clauses, filter_params = EventQueryEngine._compile_filters(query)
        clauses.extend(filter_clauses)
        params.update(filter_params)

        # -----------------------------------------------------------------
        # 3. WHERE
        # -----------------------------------------------------------------
        where = " AND ".join(clauses) if clauses else "1=1"

        # -----------------------------------------------------------------
        # 4. OPTIONS (sort / limit / offset)
        # -----------------------------------------------------------------
        order_clause = EventQueryEngine._compile_sort(query)
        limit_offset_clause, opt_params = EventQueryEngine._compile_pagination(query)

        params.update(opt_params)

        # -----------------------------------------------------------------
        # FINAL SQL
        # -----------------------------------------------------------------
        sql = f"""
            SELECT *
            FROM events
            WHERE {where}
            {order_clause}
            {limit_offset_clause}
        """

        return EventRepositoryRequestPlan(sql=sql, params=params)

    # =====================================================================
    # FIELDS
    # =====================================================================

    @staticmethod
    def _compile_fields(query: EventQuery) -> Tuple[List[str], Dict[str, Any]]:
        clauses = []
        params = {}

        for field_name, value in query.fields.model_dump(exclude_none=True).items():
            column = FIELD_COLUMN_MAP.get(field_name)
            if not column:
                continue

            param_key = f"field_{field_name}"

            clauses.append(f"{column} = :{param_key}")
            params[param_key] = value

        return clauses, params

    # =====================================================================
    # FILTERS
    # =====================================================================

    @staticmethod
    def _compile_filters(query: EventQuery) -> Tuple[List[str], Dict[str, Any]]:
        clauses = []
        params = {}

        filters = query.filters.model_dump(exclude_none=True)

        for name, value in filters.items():

            column = FILTER_COLUMN_MAP.get(name)

            # -------------------------------------------------------------
            # RANGE FILTER
            # -------------------------------------------------------------
            if isinstance(value, dict) and ("min" in value or "max" in value):
                if not column:
                    continue

                if value.get("min") is not None:
                    key = f"{name}_min"
                    clauses.append(f"{column} >= :{key}")
                    params[key] = value["min"]

                if value.get("max") is not None:
                    key = f"{name}_max"
                    clauses.append(f"{column} <= :{key}")
                    params[key] = value["max"]

            # -------------------------------------------------------------
            # NUMERIC FILTER (op, value)
            # -------------------------------------------------------------
            elif isinstance(value, dict) and "op" in value:
                if not column:
                    continue

                op_map = {
                    "gt": ">",
                    "gte": ">=",
                    "lt": "<",
                    "lte": "<=",
                    "eq": "=",
                    "neq": "!=",
                }

                op = op_map.get(value["op"])
                if not op:
                    continue

                key = f"{name}_op"
                clauses.append(f"{column} {op} :{key}")
                params[key] = value["value"]

            # -------------------------------------------------------------
            # LIST FILTER (IN clause)
            # -------------------------------------------------------------
            elif isinstance(value, list):
                if not column:
                    continue

                key = f"{name}_list"
                clauses.append(f"{column} = ANY(:{key})")
                params[key] = value

        return clauses, params

    # =====================================================================
    # OPTIONS
    # =====================================================================

    @staticmethod
    def _compile_sort(query: EventQuery) -> str:
        allowed = {
            "name": "name",
            "cross_section": "cross_section",
            "n_events": "n_events",
        }

        sort_by = allowed.get(query.options.sort_by, "name")
        order = "ASC" if query.options.order == "asc" else "DESC"

        return f"ORDER BY {sort_by} {order}"

    @staticmethod
    def _compile_pagination(query: EventQuery) -> Tuple[str, Dict[str, Any]]:
        params = {
            "limit": query.options.limit,
            "offset": query.options.offset,
        }

        clause = "LIMIT :limit OFFSET :offset"

        return clause, params