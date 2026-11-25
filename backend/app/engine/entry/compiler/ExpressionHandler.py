from __future__ import annotations

from typing import Any

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from app.engine.entry.grammar.EntryFilterLexer import EntryFilterLexer
from app.engine.entry.grammar.EntryFilterParser import EntryFilterParser
from app.models.request.where.expression.FieldExpression import (
    BooleanOperator,
    FieldExpression,
)
from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.UnaryStatement import UnaryStatement
from app.models.request.where.unary.Value import Value, ValueType


class ExpressionHandler:
    def __init__(self, raw: str) -> None:
        self.raw = raw

    def getTree(self) -> EntryFilterParser.ExpressionContext:
        """Parse the raw filter expression using the ANTLR4 lexer and parser."""
        input_stream = InputStream(self.raw)
        lexer = EntryFilterLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(ExpressionErrorListener(self.raw))
        stream = CommonTokenStream(lexer)
        parser = EntryFilterParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(ExpressionErrorListener(self.raw))
        return parser.expression()

    def generateExpression(self) -> FieldExpression:
        parsedExpression = self.getTree()
        return ExpressionHandler.generateFieldExpression(parsedExpression)

    @staticmethod
    def generateFieldExpression(
        expression: EntryFilterParser.ExpressionContext,
    ) -> FieldExpression:
        if not expression.unaryStatement():
            raise ExpressionParseError("empty expression", raw=expression.getText())
        children = [
            ExpressionHandler.generateUnaryExpression(u)
            for u in expression.unaryStatement()
        ]
        operators: list[BooleanOperator | None] = [
            ExpressionHandler.resolveBooleanOperator(op)
            for op in expression.booleanOperator()
        ]
        return FieldExpression(children=children, operators=operators)

    @staticmethod
    def generateUnaryExpression(
        expression: EntryFilterParser.UnaryStatementContext,
    ) -> UnaryStatement[Any] | FieldExpression | ListStatement:
        if expression.operator() is not None and expression.value() is not None:
            return UnaryStatement(
                operator=ExpressionHandler.resolveOperator(expression.operator()),
                value=ExpressionHandler.resolveValue(expression.value()),
            )
        if expression.listStatement() is not None:
            return ExpressionHandler.resolveList(expression.listStatement())
        if expression.expression() is not None:
            return ExpressionHandler.generateFieldExpression(expression.expression())
        raise ExpressionParseError("unrecognized expression", raw=expression.getText())

    @staticmethod
    def resolveValue(value: EntryFilterParser.ValueContext) -> Value[Any]:
        typeOf = ExpressionHandler.resolveValueType(value)
        text = value.getText()
        match typeOf:
            case ValueType.INTEGER:
                return Value(raw=text, parsed=int(text))
            case ValueType.DOUBLE | ValueType.SCIENTIFIC:
                return Value(raw=text, parsed=float(text))
            case ValueType.STRING:
                return Value(raw=text, parsed=str(text))
        raise ExpressionParseError("unsupported value type", raw=text)

    @staticmethod
    def resolveValueType(value: EntryFilterParser.ValueContext) -> ValueType:
        if value.stringValue():
            return ValueType.STRING
        if value.numberValue():
            if value.numberValue().INTEGER():
                return ValueType.INTEGER
            if value.numberValue().DOUBLE():
                return ValueType.DOUBLE
            if value.numberValue().SCIENTIFIC():
                return ValueType.SCIENTIFIC
        raise ExpressionParseError("unrecognized value type", raw=value.getText())

    @staticmethod
    def resolveOperator(operator: EntryFilterParser.OperatorContext) -> Operator:
        if operator.EQUAL():
            return Operator.EQUAL
        if operator.NOTEQUAL():
            return Operator.NOTEQUAL
        if operator.GREATERTHAN():
            return Operator.GREATERTHAN
        if operator.LESSTHAN():
            return Operator.LESSTHAN
        if operator.GREATEREQUAL():
            return Operator.GREATEREQUAL
        if operator.LESSEQUAL():
            return Operator.LESSEQUAL
        if operator.FUZZY():
            return Operator.FUZZY
        raise ExpressionParseError(
            "unrecognized operator type", raw=operator.getText()
        )

    @staticmethod
    def resolveBooleanOperator(
        operator: EntryFilterParser.BooleanOperatorContext | None,
    ) -> BooleanOperator:
        if operator is None:
            return BooleanOperator.AND
        if operator.AND():
            return BooleanOperator.AND
        if operator.OR():
            return BooleanOperator.OR
        raise ExpressionParseError(
            "unrecognized boolean operator type", raw=operator.getText()
        )

    @staticmethod
    def resolveList(listed: EntryFilterParser.ListStatementContext) -> ListStatement:
        operator = ListOperator.IN if listed.IN() else ListOperator.NOTIN
        finalList = [
            ExpressionHandler.resolveValue(element)
            for element in listed.listValue().value()
        ]
        return ListStatement(operator=operator, values=finalList)


class ExpressionParseError(ValueError):
    def __init__(self, message: str, column: int | None = None, raw: str = "") -> None:
        self.raw = raw
        self.column = column
        location = f" at column {column}" if column is not None else ""
        context = f" in '{raw}'" if raw else ""
        super().__init__(f"Invalid filter expression{location}{context}: {message}")


class ExpressionErrorListener(ErrorListener):
    def __init__(self, raw: str = "") -> None:
        super().__init__()
        self.raw = raw

    def syntaxError(
        self,
        _recognizer: Any,
        offendingSymbol: Any,
        _line: int,
        column: int,
        msg: str,
        _e: Any,
    ) -> None:
        raise ExpressionParseError(
            message=f"unexpected '{offendingSymbol}' — {msg}",
            column=column,
            raw=self.raw,
        )
