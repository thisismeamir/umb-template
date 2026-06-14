import unittest
import pytest

import unittest

import unittest

from app.engine.entry.compiler.ExpressionHandler import ExpressionHandler
from app.models.request.where.expression.FieldExpression import BooleanOperator
from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.UnaryStatement import UnaryStatement

import unittest


# Assuming ExpressionHandler, UnaryStatement, ListStatement, BooleanNode are imported

class TestEntryFilterParser(unittest.TestCase):
    TEST_SCENARIOS = {
        "int_positive": "= 42",
        "int_negative": "= -100",
        "double_positive": "!= 3.14",
        "double_negative": "!= -0.005",
        "scientific_pos": "> 1e10",
        "scientific_neg": "< -2.5E-3",
        "string_simple": "= status",
        "string_complex": "= user-node.v1_alpha",
        "op_equal": "= 1",
        "op_notequal": "!= 1",
        "op_greater_than": "> 1",
        "op_less_than": "< 1",
        "op_greater_equal": ">= 1",
        "op_less_equal": "<= 1",
        "op_fuzzy": "~ test",
        "list_in_single_int": ":in [1]",
        "list_in_multiple_int": ":in [1,2,3]",
        "list_notin_strings": "!in [apple,banana,cherry]",
        "list_mixed_types": ":in [1,-2.5,3e4,mixed-str]",
        "expr_explicit_and": "= 5 and != 10",
        "expr_explicit_or": "< 0 or > 100",
        "expr_implicit_operator": "= 5 < 10",
        "expr_multiple_booleans": "= 1 and != 2 or ~ check",
        "paren_single_clause": "(= 42)",
        "paren_nested_left": "(= 1 or = 2) and != 3",
        "paren_nested_right": "= 1 and (= 2 or = 3)",
        "paren_deeply_nested": "((= 1 or != 2) and (~ hello)) or :in [5,6]",
        "complex_kitchen_sink": "(!in [1,2e-3] or (~ pat-1 and >= -5.5)) and < 100"
    }

    # ─── 1. Basic Value Parsing Tests ─────────────────────────────────────────

    def test_positive_and_negative_integers(self):
        pos_expr = ExpressionHandler(self.TEST_SCENARIOS["int_positive"]).generateExpression()
        neg_expr = ExpressionHandler(self.TEST_SCENARIOS["int_negative"]).generateExpression()

        assert len(pos_expr.children) == 1
        assert pos_expr.children[0].value.parsed == 42

        assert len(neg_expr.children) == 1
        assert neg_expr.children[0].value.parsed == -100

    def test_double_values(self):
        pos_expr = ExpressionHandler(self.TEST_SCENARIOS["double_positive"]).generateExpression()
        neg_expr = ExpressionHandler(self.TEST_SCENARIOS["double_negative"]).generateExpression()

        assert pos_expr.children[0].value.parsed == 3.14
        assert neg_expr.children[0].value.parsed == -0.005

    def test_scientific_notation(self):
        pos_expr = ExpressionHandler(self.TEST_SCENARIOS["scientific_pos"]).generateExpression()
        neg_expr = ExpressionHandler(self.TEST_SCENARIOS["scientific_neg"]).generateExpression()

        assert pos_expr.children[0].value.parsed == 1e10
        assert neg_expr.children[0].value.parsed == -2.5e-3

    def test_unquoted_strings(self):
        simple = ExpressionHandler(self.TEST_SCENARIOS["string_simple"]).generateExpression()
        complex_str = ExpressionHandler(self.TEST_SCENARIOS["string_complex"]).generateExpression()

        assert simple.children[0].value.parsed == "status"
        assert complex_str.children[0].value.parsed == "user-node.v1_alpha"

    # ─── 2. Operator Coverage Tests ───────────────────────────────────────────

    def test_all_unary_operators(self):
        ops = ["op_equal", "op_notequal", "op_greater_than", "op_less_than",
               "op_greater_equal", "op_less_equal", "op_fuzzy"]
        expected_ops = [
            Operator.EQUAL,
            Operator.NOTEQUAL,
            Operator.GREATERTHAN,
            Operator.LESSTHAN,
            Operator.GREATEREQUAL,
            Operator.LESSEQUAL,
            Operator.FUZZY
        ]

        for scenario_key, expected_op in zip(ops, expected_ops):
            expr = ExpressionHandler(self.TEST_SCENARIOS[scenario_key]).generateExpression()
            assert expr.children[0].operator == expected_op

    # ─── 3. List Statement Tests ──────────────────────────────────────────────

    def test_list_in_operator_with_integers(self):
        single = ExpressionHandler(self.TEST_SCENARIOS["list_in_single_int"]).generateExpression()
        multiple = ExpressionHandler(self.TEST_SCENARIOS["list_in_multiple_int"]).generateExpression()

        assert single.children[0].operator == ListOperator.IN
        assert single.children[0].values[0].parsed == 1

        assert len(multiple.children[0].values) == 3
        assert [v.parsed for v in multiple.children[0].values] == [1, 2, 3]

    def test_list_notin_operator_with_strings(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["list_notin_strings"]).generateExpression()
        assert expr.children[0].operator == ListOperator.NOTIN
        assert [v.parsed for v in expr.children[0].values] == ["apple", "banana", "cherry"]

    def test_list_heterogeneous_types(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["list_mixed_types"]).generateExpression()
        parsed_vals = [v.parsed for v in expr.children[0].values]
        assert parsed_vals == [1, -2.5, 30000.0, "mixed-str"]

    # ─── 4. Expression Chain & Boolean Tests ──────────────────────────────────

    def test_explicit_boolean_and(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["expr_explicit_and"]).generateExpression()
        for child in expr.children:
            print(child)
        assert len(expr.children) == 2


    def test_explicit_boolean_or(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["expr_explicit_or"]).generateExpression()
        assert expr.operators[0] == BooleanOperator.OR

    def test_implicit_boolean_chain(self):
        # tests "= 5 < 10", Should not be parsed!
        expr = ExpressionHandler(self.TEST_SCENARIOS["expr_implicit_operator"]).generateExpression()
        assert not len(expr.children) == 2


    def test_multi_chain_boolean_mix(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["expr_multiple_booleans"]).generateExpression()
        assert len(expr.children)  == 3
        assert len(expr.operators) == 2
        assert expr.operators[0] == BooleanOperator.AND
        assert expr.operators[1] == BooleanOperator.OR
        assert expr.children[0].value.parsed == 1
        assert expr.children[0].operator == Operator.EQUAL
        assert expr.children[1].value.parsed == 2
        assert expr.children[1].operator == Operator.NOTEQUAL
        assert expr.children[2].value.parsed == "check"
        assert expr.children[2].operator == Operator.FUZZY



    # ─── 5. Grouping & Precedence (Parentheses) Tests ─────────────────────────

    def test_isolated_parentheses(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["paren_single_clause"]).generateExpression()
        # Assuming parens create a nested Expression child
        assert len(expr.children) == 1
        nested_expr = expr.children[0]
        assert nested_expr.children[0].value.parsed == 42

    def test_left_associative_parentheses(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["paren_nested_left"]).generateExpression()
        assert len(expr.children) == 2
        assert expr.children[0].children[0].value.parsed == 1
        assert expr.children[0].children[0].operator == Operator.EQUAL
        assert expr.children[0].operators[0] == BooleanOperator.OR
        assert expr.children[0].children[1].value.parsed == 2
        assert expr.children[0].children[1].operator == Operator.EQUAL

        assert expr.children[1].value.parsed == 3
        assert expr.children[1].operator == Operator.NOTEQUAL

        assert expr.operators[0] == BooleanOperator.AND



    def test_right_associative_parentheses(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["paren_nested_right"]).generateExpression()
        assert len(expr.children) == 2
        assert expr.children[1].children[0].value.parsed == 2
        assert expr.children[1].children[0].operator == Operator.EQUAL
        assert expr.children[1].operators[0] == BooleanOperator.OR
        assert expr.children[1].children[1].value.parsed == 3
        assert expr.children[1].children[1].operator == Operator.EQUAL

        assert expr.children[0].value.parsed == 1
        assert expr.children[0].operator == Operator.EQUAL

        assert expr.operators[0] == BooleanOperator.AND

    def test_deeply_nested_parentheses(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["paren_deeply_nested"]).generateExpression()
        # Just assert it didn't crash and parsed the root structure correctly
        assert len(expr.children) == 2

        assert expr.children[0].children[0].children[0].value.parsed == 1
        assert expr.children[0].children[0].children[0].operator == Operator.EQUAL

        assert expr.children[0].children[0].operators[0] == BooleanOperator.OR

        assert expr.children[0].children[0].children[1].value.parsed == 2
        assert expr.children[0].children[0].children[1].operator == Operator.NOTEQUAL

        assert expr.children[0].children[1].children[0].value.parsed == "hello"
        assert expr.children[0].children[1].children[0].operator == Operator.FUZZY

    # ─── 6. High-Complexity End-to-End Test ───────────────────────────────────

    def test_kitchen_sink_expression(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["complex_kitchen_sink"]).generateExpression()
        assert len(expr.children) == 2  # The big grouped block, then the implicit "< 100"
        assert expr.children[1].operator == Operator.LESSTHAN
        assert expr.children[1].value.parsed == 100


class TestEntryFilterParserExtended(unittest.TestCase):
    TEST_SCENARIOS = {
        "val_zero": "= 0",
        "val_negative_zero": "= -0",
        "val_large_int": "= 999999999999999999999",
        "val_double_no_leading_zero": "= .5",
        "val_scientific_capital_e": "< 1.21E14",
        "val_scientific_explicit_plus": "> 5e+10",
        "val_string_alphanumeric_start": "= 1st-place_item",
        "val_string_complex_chars": "= a.b-c_d.1-2_3",
        "val_string_single_char": "= x",
        "ws_no_spaces": "=5and!=10",
        "ws_excessive_spaces": "=     42    and   <   10",
        "ws_tabs_and_newlines": ">\n\t100\n\tor\n\t=\t50",
        "ws_empty_string": "",
        "implicit_two_statements": "= 5 != 10",
        "implicit_three_statements": "> 0 < 100 != 50",
        "implicit_mixed_with_explicit": "= 1 = 2 and = 3 = 4 or = 5",
        "implicit_with_lists": ":in [1,2] !in [3,4] ~ test",
        "list_single_item": ":in [42]",
        "list_massive_length": ":in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]",
        "list_scientific_mix": "!in [1e-5, 2E10, -3.14e+2]",
        "list_string_mix": ":in [apple, banana-split, cherry.pie_v1]",
        "list_nested_brackets": ":in [[1,2], 3]",
        "nest_deep_left": "((((= 1) and = 2) or = 3) and = 4)",
        "nest_deep_right": "= 1 and (= 2 or (= 3 and (= 4)))",
        "nest_redundant_parens": "((((= 42))))",
        "nest_parens_in_lists_invalid": ":in [(1)]",
        "boss_fight_valid": "(((> -1.5e3 and !in [dev-1, test.2]) or (~ fuzzy_match_123)) :in [10, 20] and (= 0 or < 100))",
        "err_missing_value": "=",
        "err_missing_list_bracket": ":in [1, 2",
        "err_trailing_comma_list": ":in [1, 2, ]",
        "err_unbalanced_parens_left": "(= 1 and = 2",
        "err_unbalanced_parens_right": "= 1 and = 2)",
        "err_invalid_operator": "+ 5",
        "err_quoted_string": "= \"hello\"",
        "err_invalid_string_char": "= hello@world",
        "err_consecutive_operators": "= > 5"
    }

    # ─── 1. LEXER AMBIGUITIES & EDGE VALUES ────────────────────────────────────

    def test_numeric_boundaries(self):
        zero = ExpressionHandler(self.TEST_SCENARIOS["val_zero"]).generateExpression()
        neg_zero = ExpressionHandler(self.TEST_SCENARIOS["val_negative_zero"]).generateExpression()
        huge = ExpressionHandler(self.TEST_SCENARIOS["val_large_int"]).generateExpression()

        assert zero.children[0].value.parsed == 0
        assert neg_zero.children[0].value.parsed == 0
        assert huge.children[0].value.parsed == 999999999999999999999

    def test_string_vs_integer_resolution(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["val_string_alphanumeric_start"]).generateExpression()
        assert type(expr.children[0].value.parsed) is str
        assert expr.children[0].value.parsed == "1st-place_item"

    def test_string_allowed_characters(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["val_string_complex_chars"]).generateExpression()
        assert expr.children[0].value.parsed == "a.b-c_d.1-2_3"

    # ─── 2. WHITESPACE HANDLING ────────────────────────────────────────────────

    def test_excessive_whitespace(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["ws_excessive_spaces"]).generateExpression()
        assert len(expr.children) == 2
        assert expr.children[0].value.parsed == 42
        assert expr.children[1].value.parsed == 10

    def test_missing_optional_whitespace(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["ws_no_spaces"]).generateExpression()
        assert len(expr.children) == 2
        assert expr.children[0].operator == "="
        assert expr.children[1].operator == "!="

    # ─── 3. IMPLICIT BOOLEAN OPERATORS ─────────────────────────────────────────

    def test_implicit_operator_chaining(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["implicit_three_statements"]).generateExpression()
        assert len(expr.children) == 3
        assert expr.children[0].value.parsed == 0
        assert expr.children[1].value.parsed == 100
        assert expr.children[2].value.parsed == 50

    def test_implicit_mixed_with_explicit(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["implicit_mixed_with_explicit"]).generateExpression()
        # Nodes: Unary, Unary, AND, Unary, Unary, OR, Unary -> Total 7 top-level nodes
        assert len(expr.children) == 7
        assert expr.children[2].operator == "and"
        assert expr.children[5].operator == "or"

    # ─── 4. ADVANCED LIST SCENARIOS ────────────────────────────────────────────

    def test_list_single_element(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["list_single_item"]).generateExpression()
        assert len(expr.children[0].values) == 1

    def test_list_massive_payload(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["list_massive_length"]).generateExpression()
        assert len(expr.children[0].values) == 15
        assert expr.children[0].values[-1].parsed == 15

    def test_list_heterogeneous_complex_mix(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["list_scientific_mix"]).generateExpression()
        assert expr.children[0].values[0].parsed == 1e-5
        assert expr.children[0].values[1].parsed == 2e10
        assert expr.children[0].values[2].parsed == -314.0

    # ─── 5. EXTREME NESTING & PRECEDENCE ───────────────────────────────────────

    def test_redundant_parentheses(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["nest_redundant_parens"]).generateExpression()
        # Drill down 4 layers to find the unary statement
        inner = expr.children[0].children[0].children[0].children[0]
        assert inner.value.parsed == 42

    def test_deep_associativity_left_and_right(self):
        left = ExpressionHandler(self.TEST_SCENARIOS["nest_deep_left"]).generateExpression()
        right = ExpressionHandler(self.TEST_SCENARIOS["nest_deep_right"]).generateExpression()

        # Verify roots parsed cleanly without raising exceptions
        assert len(left.children) == 3
        assert len(right.children) == 3

    # ─── 6. MAXIMUM COMPLEXITY ─────────────────────────────────────────────────

    def test_boss_fight_expression(self):
        expr = ExpressionHandler(self.TEST_SCENARIOS["boss_fight_valid"]).generateExpression()
        # Simply asserting it doesn't crash is often enough for the boss fight,
        # but we can verify it contains multiple chained groups at the top level
        assert len(expr.children) == 3
        assert expr.children[1].operator == "and"

    # ─── 7. NEGATIVE TESTING (EXPECTED FAILURES) ───────────────────────────────
    # Depending on your parser configuration, replace `Exception` with your specific
    # syntax error class (e.g., `antlr4.error.Errors.ParseCancellationException`)

    def test_fail_on_missing_values(self):
        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_missing_value"]).generateExpression()

    def test_fail_on_malformed_lists(self):
        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_missing_list_bracket"]).generateExpression()

        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_trailing_comma_list"]).generateExpression()

    def test_fail_on_unbalanced_parentheses(self):
        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_unbalanced_parens_left"]).generateExpression()

        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_unbalanced_parens_right"]).generateExpression()

    def test_fail_on_illegal_characters(self):
        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_quoted_string"]).generateExpression()

        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_invalid_string_char"]).generateExpression()

    def test_fail_on_consecutive_operators(self):
        with self.assertRaises(Exception):
            ExpressionHandler(self.TEST_SCENARIOS["err_consecutive_operators"]).generateExpression()