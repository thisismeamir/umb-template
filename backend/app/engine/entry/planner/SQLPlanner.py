from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass
from typing import Any

from app.engine.entry.compiler.ExpressionHandler import (
    ExpressionHandler,
    ExpressionParseError,
)
from app.models.request.AggregateStatementModel import AggregateFunction
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.request.PathTrees import MetadataPathTree
from app.models.request.SortStatementModel import SortStatementOrder
from app.models.request.where.expression.FieldExpression import (
    BooleanOperator,
    FieldExpression,
)
from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.UnaryStatement import UnaryStatement
from app.utility.PathTreeToList import conditionTreeToList, pathTreeToList


@dataclass
class SQLFragment:
    sql: str
    params: list[Any]


JSONPATH_OPERATOR_MAP: dict[Operator, str] = {
    Operator.EQUAL: "==",
    Operator.NOTEQUAL: "!=",
    Operator.GREATERTHAN: ">",
    Operator.LESSTHAN: "<",
    Operator.GREATEREQUAL: ">=",
    Operator.LESSEQUAL: "<=",
}

AGGREGATE_SQL_MAP: dict[AggregateFunction, str] = {
    AggregateFunction.COUNT: "COUNT",
    AggregateFunction.SUM: "SUM",
    AggregateFunction.AVG: "AVG",
    AggregateFunction.MIN: "MIN",
    AggregateFunction.MAX: "MAX",
}

FUZZY_SIMILARITY_THRESHOLD: float = 0.3


class SQLPlanner:
    """Compiles an EntityRequestModel into parameterized PostgreSQL SQL fragments."""

    def __init__(self, request: EntityRequestModel) -> None:
        self.request: EntityRequestModel = request

    # ─── Public Plan Builders ─────────────────────────────────────────

    def generatePlan(self) -> SQLFragment:
        """Build the primary entity SELECT query with filters, sorting, and pagination."""
        wherePlan = self._buildWhereClause(includeCursor=True)
        sortPlan = self.getSortClause()
        limitPlan = self.getLimitClause()

        selectFragment = SQLFragment(sql="SELECT id, metadata FROM entries", params=[])
        whereFragment = SQLFragment(
            sql=f"WHERE {wherePlan.sql}" if wherePlan.sql else "",
            params=wherePlan.params,
        )

        combined = self._concatFragments(
            [selectFragment, whereFragment, sortPlan, limitPlan],
            separator=" ",
        )
        return self._bindPlaceholders(combined)

    def generateCountPlan(self) -> SQLFragment:
        """Build a COUNT(*) query using all active selection and filter clauses."""
        wherePlan = self._buildWhereClause(includeCursor=False)
        selectFragment = SQLFragment(sql="SELECT COUNT(*) AS count FROM entries", params=[])
        whereFragment = SQLFragment(
            sql=f"WHERE {wherePlan.sql}" if wherePlan.sql else "",
            params=wherePlan.params,
        )
        combined = self._concatFragments([selectFragment, whereFragment], separator=" ")
        return self._bindPlaceholders(combined)

    def generateAggregatePlan(self) -> tuple[list[str], SQLFragment]:
        """Build an aggregate (count/sum/avg/min/max) query over a single metadata path."""
        agg = self.request.aggregate
        if agg is None:
            raise ValueError("aggregate clause is required")
        paths = pathTreeToList(agg.by)
        if len(paths) != 1:
            raise ValueError("aggregate.by must specify exactly one path")

        path = paths[0]
        jsonpath = self._formatJsonPath(path)
        sqlFn = AGGREGATE_SQL_MAP[agg.fn]

        if agg.fn == AggregateFunction.COUNT:
            aggExpr = "COUNT(jsonb_path_query_first(metadata, ?))"
        else:
            aggExpr = (
                f"{sqlFn}((jsonb_path_query_first(metadata, ?) #>> '{{}}')::double precision)"
            )

        selectFragment = SQLFragment(
            sql=f"SELECT {aggExpr} AS value FROM entries",
            params=[jsonpath],
        )
        wherePlan = self._buildWhereClause(includeCursor=False)
        whereFragment = SQLFragment(
            sql=f"WHERE {wherePlan.sql}" if wherePlan.sql else "",
            params=wherePlan.params,
        )
        combined = self._concatFragments([selectFragment, whereFragment], separator=" ")
        return path, self._bindPlaceholders(combined)

    def generateDistinctPlan(self) -> tuple[list[str], SQLFragment]:
        """Build a SELECT DISTINCT query returning all unique values at a metadata path."""
        if self.request.distinct is None:
            raise ValueError("distinct clause is required")
        paths = pathTreeToList(self.request.distinct)
        if len(paths) != 1:
            raise ValueError("distinct must specify exactly one path")

        path = paths[0]
        jsonpath = self._formatJsonPath(path)
        selectFragment = SQLFragment(
            sql="SELECT DISTINCT jsonb_path_query_first(metadata, ?) AS value FROM entries",
            params=[jsonpath],
        )
        wherePlan = self._buildWhereClause(includeCursor=False)
        notNullFragment = SQLFragment(
            sql="jsonb_path_exists(metadata, ?)",
            params=[f"{jsonpath}?(@ != null)"],
        )
        fullWhere = self._concatFragments([wherePlan, notNullFragment], separator=" AND ")
        whereFragment = SQLFragment(
            sql=f"WHERE {fullWhere.sql}" if fullWhere.sql else "",
            params=fullWhere.params,
        )
        combined = self._concatFragments([selectFragment, whereFragment], separator=" ")
        return path, self._bindPlaceholders(combined)

    def generateVersionsPlan(self) -> SQLFragment:
        """Build a version history query for an entity id with optional versions filters."""
        if self.request.id is None:
            raise ValueError("versions query requires 'id'")
        clauses = ["id = ?"]
        params: list[Any] = [self.request.id]
        v = self.request.versions
        order = "DESC"
        limit: int | None = None

        if v is not None:
            if v.by is not None:
                clauses.append("created_by = ?")
                params.append(v.by)
            if v.type is not None:
                clauses.append("entry_type = ?")
                params.append(v.type)
            if v.before is not None:
                clauses.append("created_at < ?")
                params.append(v.before)
            if v.after is not None:
                clauses.append("created_at > ?")
                params.append(v.after)
            if v.first is not None:
                order = "ASC"
                limit = v.first
            elif v.last is not None:
                order = "DESC"
                limit = v.last

        sql = (
            "SELECT id, version, created_at, created_by, source FROM entries "
            f"WHERE {' AND '.join(clauses)} ORDER BY version {order}"
        )
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        return self._bindPlaceholders(SQLFragment(sql=sql, params=params))

    def generateRandomPlan(self, limit: int = 1) -> SQLFragment:
        """Build a query returning N random current entries (optionally filtered)."""
        wherePlan = self._buildWhereClause(includeCursor=False)
        selectFragment = SQLFragment(sql="SELECT id, metadata FROM entries", params=[])
        whereFragment = SQLFragment(
            sql=f"WHERE {wherePlan.sql}" if wherePlan.sql else "",
            params=wherePlan.params,
        )
        orderLimit = SQLFragment(sql="ORDER BY RANDOM() LIMIT ?", params=[limit])
        combined = self._concatFragments(
            [selectFragment, whereFragment, orderLimit],
            separator=" ",
        )
        return self._bindPlaceholders(combined)

    # ─── Shared WHERE Assembly ────────────────────────────────────────

    def _buildWhereClause(self, *, includeCursor: bool) -> SQLFragment:
        parts = [
            self.getEntrySelectionStatement(),
            self.getContainStatement(),
            self.getWithoutStatement(),
            self.getWhereStatements(),
            self.getSearchStatement(),
        ]
        if includeCursor:
            parts.append(self.getCursorClause())
        return self._concatFragments(parts, separator=" AND ")

    # ─── Entry Selection ──────────────────────────────────────────────

    def getEntrySelectionStatement(self) -> SQLFragment:
        r = self.request
        clauses: list[str] = []
        params: list[Any] = []

        if r.entry_type is not None:
            types = r.entry_type if isinstance(r.entry_type, list) else [r.entry_type]
            clauses.append("entry_type = ANY(?)")
            params.append(types)
        if r.id is not None:
            clauses.append("id = ?")
            params.append(r.id)
        if r.version is not None:
            clauses.append("version = ?")
            params.append(r.version)
        elif r.snapshot is None:
            clauses.append("is_current = TRUE")
        if r.snapshot is not None:
            clauses.append("created_at <= ?")
            params.append(r.snapshot)

        return SQLFragment(sql=" AND ".join(clauses), params=params)

    # ─── contains & without ───────────────────────────────────────────

    def getContainStatement(self) -> SQLFragment:
        if self.request.contains is not None:
            return self.buildJsonPathWhereClause(self.request.contains, negate=False)
        return SQLFragment("", [])

    def getWithoutStatement(self) -> SQLFragment:
        if self.request.without is not None:
            return self.buildJsonPathWhereClause(self.request.without, negate=True)
        return SQLFragment("", [])

    def buildJsonPathWhereClause(
        self,
        condition_tree: MetadataPathTree,
        column_name: str = "metadata",
        *,
        negate: bool = False,
    ) -> SQLFragment:
        entries = pathTreeToList(condition_tree)
        clauses: list[str] = []
        params: list[Any] = []
        prefix = "NOT " if negate else ""
        for path in entries:
            json_path = f"{self._formatJsonPath(path)}?(@ != null)"
            clauses.append(f"{prefix}jsonb_path_exists({column_name}, ?)")
            params.append(json_path)
        return SQLFragment(sql=" AND ".join(clauses), params=params)

    # ─── where ────────────────────────────────────────────────────────

    def getWhereStatements(self) -> SQLFragment:
        if self.request.where is None:
            return SQLFragment("", [])
        statements = conditionTreeToList(self.request.where)
        fragments: list[SQLFragment] = []
        for path, raw in statements:
            expr = ExpressionHandler(raw).generateExpression()
            fragments.append(self.renderFieldExpression(path, expr))
        return self._concatFragments(fragments, separator=" AND ")

    def renderFieldExpression(
        self, path: list[str], expr: FieldExpression
    ) -> SQLFragment:
        rendered = [self.renderChild(path, c) for c in expr.children]
        sql = rendered[0].sql
        params = list(rendered[0].params)
        for i, op in enumerate(expr.operators):
            if op == BooleanOperator.AND or op is None:
                joiner = " AND "
            elif op == BooleanOperator.OR:
                joiner = " OR "
            else:
                raise ExpressionParseError(
                    f"unrecognized boolean operator: {op}", raw=""
                )
            sql += joiner + rendered[i + 1].sql
            params += rendered[i + 1].params
        return SQLFragment(sql=f"({sql})", params=params)

    def renderChild(
        self, path: list[str], child: UnaryStatement[Any] | ListStatement | FieldExpression
    ) -> SQLFragment:
        if isinstance(child, UnaryStatement):
            return self.renderUnaryStatement(path, child)
        if isinstance(child, ListStatement):
            return self.renderListStatement(path, child)
        if isinstance(child, FieldExpression):
            return self.renderFieldExpression(path, child)
        raise ExpressionParseError(f"unrecognized child type: {type(child)}", raw="")

    def renderUnaryStatement(
        self, path: list[str], stmt: UnaryStatement[Any]
    ) -> SQLFragment:
        jsonpath = self._formatJsonPath(path)
        if stmt.operator == Operator.FUZZY:
            sql = (
                "EXISTS ("
                "SELECT 1 FROM jsonb_path_query(metadata, ?) AS val "
                f"WHERE similarity(val #>> '{{}}', ?) > {FUZZY_SIMILARITY_THRESHOLD}"
                ")"
            )
            return SQLFragment(sql=sql, params=[jsonpath, str(stmt.value.parsed)])
        op = JSONPATH_OPERATOR_MAP[stmt.operator]
        value = json.dumps(stmt.value.parsed)
        filter_expr = f"{jsonpath} ? (@ {op} {value})"
        return SQLFragment(sql="jsonb_path_exists(metadata, ?)", params=[filter_expr])

    def renderListStatement(
        self, path: list[str], stmt: ListStatement
    ) -> SQLFragment:
        jsonpath = self._formatJsonPath(path)
        comparisons = " || ".join(f"@ == {json.dumps(v.parsed)}" for v in stmt.values)
        filter_expr = f"{jsonpath} ? ({comparisons})"
        sql = "jsonb_path_exists(metadata, ?)"
        if stmt.operator == ListOperator.NOTIN:
            sql = f"NOT {sql}"
        return SQLFragment(sql=sql, params=[filter_expr])

    # ─── search ───────────────────────────────────────────────────────

    def getSearchStatement(self) -> SQLFragment:
        if self.request.search is None:
            return SQLFragment("", [])
        sql = (
            "EXISTS ("
            "SELECT 1 FROM jsonb_path_query(metadata, '$.**') AS val "
            "WHERE jsonb_typeof(val) NOT IN ('object', 'array') "
            f"AND similarity(val #>> '{{}}', ?) > {FUZZY_SIMILARITY_THRESHOLD}"
            ")"
        )
        return SQLFragment(sql=sql, params=[self.request.search])

    # ─── sort & pagination ────────────────────────────────────────────

    def getSortClause(self) -> SQLFragment:
        if self.request.sort is None:
            if self.request.page is not None:
                return SQLFragment(sql="ORDER BY id ASC", params=[])
            return SQLFragment("", [])
        s = self.request.sort
        paths = pathTreeToList(s.by)
        if len(paths) != 1:
            raise ValueError("sort.by must specify exactly one path")
        jsonpath = self._formatJsonPath(paths[0])
        order = "DESC" if s.order == SortStatementOrder.DESC else "ASC"
        sql = f"ORDER BY jsonb_path_query_first(metadata, ?) {order} NULLS LAST, id ASC"
        return SQLFragment(sql=sql, params=[jsonpath])

    def getCursorClause(self) -> SQLFragment:
        if self.request.page is None or self.request.page.cursor is None:
            return SQLFragment("", [])
        return SQLFragment(sql="id > ?::uuid", params=[self.request.page.cursor])

    def getLimitClause(self) -> SQLFragment:
        if self.request.page is None:
            return SQLFragment("", [])
        # Fetch size + 1 to detect whether a subsequent page exists
        return SQLFragment(sql="LIMIT ?", params=[self.request.page.size + 1])

    # ─── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _formatJsonPath(path: list[str]) -> str:
        if path == ["*"]:
            return "$.**"
        formatted_segments = ".".join(json.dumps(k) for k in path)
        return f"$.**.{formatted_segments}"

    @staticmethod
    def _concatFragments(
        fragments: list[SQLFragment], separator: str = " AND "
    ) -> SQLFragment:
        parts = [f.sql for f in fragments if f.sql]
        params = [p for f in fragments for p in f.params]
        return SQLFragment(sql=separator.join(parts), params=params)

    @staticmethod
    def _bindPlaceholders(fragment: SQLFragment) -> SQLFragment:
        """Convert all ? placeholders to PostgreSQL $1, $2, ... in a single top-level pass."""
        counter = itertools.count(1)
        sql = re.sub(r"\?", lambda _: f"${next(counter)}", fragment.sql)
        return SQLFragment(sql=sql, params=fragment.params)
