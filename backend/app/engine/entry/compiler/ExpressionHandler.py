from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener
from pydantic_core.core_schema import ErrorType

from app.engine.entry.grammar.EntryFilterLexer import EntryFilterLexer
from app.engine.entry.grammar.EntryFilterParser import EntryFilterParser
from app.models.request.where.expression.FieldExpression import FieldExpression, BooleanOperator
from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.UnaryStatement import UnaryStatement
from app.models.request.where.unary.Value import Value, ValueType

    

class ExpressionHandler:
    def __init__(self, raw: str):
        self.raw = raw

    def getTree(self) -> EntryFilterParser.ExpressionContext:
        """
        Using the parser and lexer, get the tree of the expression.
        :return:
        """
        input_stream = InputStream(self.raw)
        lexer = EntryFilterLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(ExpressionErrorListener(self.raw))
        stream = CommonTokenStream(lexer)
        parser = EntryFilterParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(ExpressionErrorListener(self.raw))
        ### Check if everything is alright before returning
        ## What to do here
        return parser.expression()

    def generateExpression(self) -> FieldExpression:
        parsedExpression = self.getTree()
        return ExpressionHandler.generateFieldExpression(parsedExpression)


    @staticmethod
    def generateFieldExpression(expression: EntryFilterParser.ExpressionContext) -> FieldExpression:
        if not expression.unaryStatement():
            raise ExpressionParseError("empty expression", raw=expression.getText())
        children = [ExpressionHandler.generateUnaryExpression(u) for u in expression.unaryStatement()]
        operators = [ExpressionHandler.resolveBooleanOperator(op) for op in expression.booleanOperator()]

        return FieldExpression(children=children, operators=operators)

    @staticmethod
    def generateUnaryExpression(
            expression: EntryFilterParser.UnaryStatementContext) -> UnaryStatement | FieldExpression | ListStatement:
        if expression.operator() is not None and expression.value() is not None:
            return UnaryStatement(
                operator=ExpressionHandler.resolveOperator(expression.operator()),
                value=ExpressionHandler.resolveValue(expression.value())
            )
        elif expression.listStatement() is not None:
            return ExpressionHandler.resolveList(expression.listStatement())
        elif expression.expression() is not None:
            return ExpressionHandler.generateFieldExpression(expression.expression())

        raise ExpressionParseError("unrecognized expression", raw=expression.getText())

    @staticmethod
    def resolveValue(value: EntryFilterParser.ValueContext) -> Value:
        typeOf = ExpressionHandler.resolveValueType(value)
        match typeOf:
            case ValueType.INTEGER:
                return Value(
                    raw=value.getText(),
                    parsed=int(value.getText()),
                )
            case ValueType.DOUBLE:
                return Value(
                    raw=value.getText(),
                    parsed=float(value.getText()),
                )
            case ValueType.SCIENTIFIC:
                return Value(
                    raw=value.getText(),
                    parsed=float(value.getText()),
                )
            case ValueType.STRING:
                return Value(
                    raw=value.getText(),
                    parsed=str(value.getText()),
                )

        # TODO: Warning about the type? what is this


    @staticmethod
    def resolveValueType(value: EntryFilterParser.ValueContext) -> ValueType:
        if value.stringValue():
            return ValueType.STRING
        elif value.numberValue():
            if value.numberValue().INTEGER():
                return ValueType.INTEGER
            elif value.numberValue().DOUBLE():
                return ValueType.DOUBLE
            elif value.numberValue().SCIENTIFIC():
                return ValueType.SCIENTIFIC
        raise ExpressionParseError("unrecognized value type", raw=value.getText())

    @staticmethod
    def resolveOperator(operator: EntryFilterParser.OperatorContext) -> Operator:
        if operator.EQUAL():
            return Operator.EQUAL
        elif operator.NOTEQUAL():
            return Operator.NOTEQUAL
        elif operator.GREATERTHAN():
            return Operator.GREATERTHAN
        elif operator.LESSTHAN():
            return Operator.LESSTHAN
        elif operator.GREATEREQUAL():
            return Operator.GREATEREQUAL
        elif operator.LESSEQUAL():
            return Operator.LESSEQUAL
        elif operator.FUZZY():
            return Operator.FUZZY
        else:
            raise ExpressionParseError("unrecognized operator type", raw=operator.getText())

    @staticmethod
    def resolveBooleanOperator(operator: EntryFilterParser.BooleanOperatorContext) -> BooleanOperator:
        if operator.AND():
            return BooleanOperator.AND
        elif operator.OR():
            return BooleanOperator.OR
        elif operator is None:
            return BooleanOperator.AND
        else:
            raise ExpressionParseError("unrecognized boolean operator operator type", raw=operator.getText())

    @staticmethod
    def resolveList(listed: EntryFilterParser.ListStatementContext) -> ListStatement:
        if listed.IN():
            operator = ListOperator.IN
        else:
            operator = ListOperator.NOTIN
        finalList = []
        for element in listed.listValue().value():
            finalList.append(
                ExpressionHandler.resolveValue(element)
            )
        return ListStatement(
            operator=operator,
            values=finalList
        )

class ExpressionParseError(ValueError):
    def __init__(self, message: str, column: int | None = None, raw: str = ""):
        self.raw = raw
        self.column = column
        location = f" at column {column}" if column is not None else ""
        context = f" in '{raw}'" if raw else ""
        super().__init__(f"Invalid filter expression{location}{context}: {message}")

class ExpressionErrorListener(ErrorListener):
    def __init__(self, raw: str = ""):
        super().__init__()
        self.raw = raw

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise ExpressionParseError(
            message=f"unexpected '{offendingSymbol}' — {msg}",
            column=column,
            raw=self.raw
        )
