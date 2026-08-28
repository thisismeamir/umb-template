from dataclasses import dataclass
import json
import itertools
import re
from app.engine.entry.compiler.ExpressionHandler import ExpressionHandler
from app.models.request import where
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.request.PathTrees import MetadataPathTree
from app.utility import PathTreeToList
from app.utility.PathTreeToList import conditionTreeToList
from app.models.request.PathTrees import MetadataPathTree
from app.models.entry.EntryBaseModel import *
from app.models.entry.EntryModel import *
from app.models.request.where.unary.UnaryStatement import *
from app.models.request.where.expression.FieldExpression import *
from app.models.request.where.unary.Operator import *
from app.models.request.EntityRequestModel  import *
from app.engine.entry.compiler.ExpressionHandler import *

@dataclass
class SQLFragment:
    sql: str
    params: list

JSONPATH_OPERATOR_MAP = {
    Operator.EQUAL: "==",
    Operator.NOTEQUAL: "!=",
    Operator.GREATERTHAN: ">",
    Operator.LESSTHAN: "<",
    Operator.GREATEREQUAL: ">=",
    Operator.LESSEQUAL: "<=",
}

class SQLPlanner:
    def __init__(self, request: EntityRequestModel):
        self.request: EntityRequestModel = request

    def generatePlan(self) -> SQLFragment:
        wherePlan = SQLPlanner.mergeFragments(
            [
                self.getEntrySelectionStatement(),
                self.getContainStatment(),
                self.getWhereStatements(),
                self.getSearchStatement(),
            ],
            separator=" AND ",
        )
        distinctPlan = self.getDistinctClause()
        sortPlan = self.getSortClause()

        selectFragment = SQLFragment(
            sql="SELECT " + (distinctPlan.sql + " " if distinctPlan.sql else "") + "id, metadata FROM entries",
            params=distinctPlan.params,
        )
        whereFragment = SQLFragment(
            sql=f"WHERE {wherePlan.sql}" if wherePlan.sql else "",
            params=wherePlan.params,
        )

        final = SQLPlanner.mergeFragments(
            [selectFragment, whereFragment, sortPlan],
            separator=" ",
        )
        return final

    # ─── Entry Selection ─────────────────────────────────────────────

    def getEntrySelectionStatement(self) -> SQLFragment:
        r = self.request
        clauses = []
        params = []
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
        else:
            clauses.append("is_current = TRUE")
        if r.snapshot is not None:
            clauses.append("created_at <= ?")
            params.append(r.snapshot)
        sql = " AND ".join(clauses)
        return SQLFragment(sql=sql, params=params)

    # ─── contains ─────────────────────────────────────────────────────

    def getContainStatment(self) -> SQLFragment:
        if self.request.contains is not None:
            return self.buildJsonPathWhereClause(self.request.contains)
        return SQLFragment("", [])

    def buildJsonPathWhereClause(
        self, condition_tree: MetadataPathTree, column_name: str = "metadata"
    ) -> SQLFragment:
        """Transforms a MetadataPathTree into a parameterized SQLFragment using
        jsonb_path_exists() expressions for each path structure.
        """
        entries = pathTreeToList(condition_tree)
        clauses = []
        params = []
        for path in entries:
            formatted_segments = ".".join(json.dumps(key) for key in path)
            json_path = f"$.**.{formatted_segments}?(@ != null)"
            clauses.append(f"jsonb_path_exists({column_name}, ?)")
            params.append(json_path)
        sql = " AND \n  ".join(clauses)
        return SQLFragment(sql=sql, params=params)

    # ─── where ────────────────────────────────────────────────────────

    def getWhereStatements(self) -> SQLFragment:
        if self.request.where is None:
            return SQLFragment("", [])
        statements = conditionTreeToList(self.request.where)
        fragments = []
        for path, raw in statements:
            expr = ExpressionHandler(raw).generateExpression()
            fragments.append(self.renderFieldExpression(path, expr))
        sql = " AND ".join(f.sql for f in fragments if f.sql)
        params = [p for f in fragments for p in f.params]
        return SQLFragment(sql=sql, params=params)

    def renderFieldExpression(
        self, path: list[str], expr: FieldExpression
    ) -> SQLFragment:
        rendered = [self.renderChild(path, c) for c in expr.children]
        sql = rendered[0].sql
        params = list(rendered[0].params)
        for i, op in enumerate(expr.operators):
            if op == BooleanOperator.AND:
                joiner = " AND "
            elif op == BooleanOperator.OR:
                joiner = " OR "
            elif op is None:
                continue
            else:
                raise ExpressionParseError(
                    f"unrecognized boolean operator: {op}", raw=""
                )
            sql += joiner + rendered[i + 1].sql
            params += rendered[i + 1].params
        return SQLFragment(sql=f"({sql})", params=params)

    def renderChild(
        self, path: list[str], child: UnaryStatement | ListStatement | FieldExpression
    ) -> SQLFragment:
        if isinstance(child, UnaryStatement):
            return self.renderUnaryStatement(path, child)
        elif isinstance(child, ListStatement):
            return self.renderListStatement(path, child)
        elif isinstance(child, FieldExpression):
            return self.renderFieldExpression(path, child)
        raise ExpressionParseError(f"unrecognized child type: {type(child)}", raw="")

    def renderUnaryStatement(
        self, path: list[str], stmt: UnaryStatement
    ) -> SQLFragment:
        jsonpath = "$.**." + ".".join(json.dumps(k) for k in path)
        if stmt.operator == Operator.FUZZY:
            sql = """EXISTS (
                SELECT 1 FROM jsonb_path_query(metadata, ?) AS val
                WHERE similarity(val #>> '{}', ?) > 0.3
            )"""
            return SQLFragment(sql=sql, params=[jsonpath, stmt.value.parsed])
        op = JSONPATH_OPERATOR_MAP[stmt.operator]
        value = json.dumps(stmt.value.parsed)
        filter_expr = f"{jsonpath} ? (@ {op} {value})"
        return SQLFragment(sql="jsonb_path_exists(metadata, ?)", params=[filter_expr])

    def renderListStatement(self, path: list[str], stmt: ListStatement) -> SQLFragment:
        jsonpath = "$.**." + ".".join(json.dumps(k) for k in path)
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
        sql = """EXISTS (
            SELECT 1 FROM jsonb_path_query(metadata, '$.**') AS val
            WHERE jsonb_typeof(val) NOT IN ('object', 'array')
              AND similarity(val #>> '{}', ?) > 0.3
        )"""
        return SQLFragment(sql=sql, params=[self.request.search])

    # ─── distinct ─────────────────────────────────────────────────────

    def getDistinctClause(self) -> SQLFragment:
        if self.request.distinct is None:
            return SQLFragment("", [])
        paths = pathTreeToList(self.request.distinct)
        exprs = []
        for path in paths:
            formatted_segments = ".".join(json.dumps(k) for k in path)
            exprs.append(f"jsonb_path_query_first(metadata, '$.**.{formatted_segments}')")
        sql = "DISTINCT ON (" + ", ".join(exprs) + ")"
        return SQLFragment(sql=sql, params=[])

    # ─── Sorting ─────────────────────────────────────────────────

    def getSortClause(self) -> SQLFragment:
        if self.request.sort is None:
            return SQLFragment("", [])
        s = self.request.sort
        paths = pathTreeToList(s.by)
        if len(paths) != 1:
            raise ValueError("sort.by must specify exactly one path")
        formatted_segments = ".".join(json.dumps(k) for k in paths[0])
        expr = f"jsonb_path_query_first(metadata, '$.**.{formatted_segments}')"
        order = "DESC" if s.order == "desc" else "ASC"
        sql = f"ORDER BY {expr} {order} NULLS LAST"
        return SQLFragment(sql=sql, params=[])

    # ─── merge helper ─────────────────────────────────────────────────

    @staticmethod
    def mergeFragments(
        fragments: list[SQLFragment], separator: str = " AND "
    ) -> SQLFragment:
        parts = [f.sql for f in fragments if f.sql]
        params = [p for f in fragments for p in f.params]
        sql = separator.join(parts)
        counter = itertools.count(1)
        sql = re.sub(r"\?", lambda _: f"${next(counter)}", sql)
        return SQLFragment(sql=sql, params=params)

if __name__ == "__main__":
    request = EntityRequestModel(
        contains={"campaign": {}, "event_number": {}},
        where={"ecm": ">10 and <100", "parent": {"generator": {"version": "=8.3"}}},
    )

    sqlPlanner = SQLPlanner(request)
    plan = sqlPlanner.generatePlan()
    print("=== SQL ===")
    print(plan.sql)
    print("=== PARAMS ===")
    print(plan.params)
