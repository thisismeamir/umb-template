# Generated from EntryFilter.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .EntryFilterParser import EntryFilterParser
else:
    from EntryFilterParser import EntryFilterParser

# This class defines a complete listener for a parse tree produced by EntryFilterParser.
class EntryFilterListener(ParseTreeListener):

    # Enter a parse tree produced by EntryFilterParser#expression.
    def enterExpression(self, ctx:EntryFilterParser.ExpressionContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#expression.
    def exitExpression(self, ctx:EntryFilterParser.ExpressionContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#unaryStatement.
    def enterUnaryStatement(self, ctx:EntryFilterParser.UnaryStatementContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#unaryStatement.
    def exitUnaryStatement(self, ctx:EntryFilterParser.UnaryStatementContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#listStatement.
    def enterListStatement(self, ctx:EntryFilterParser.ListStatementContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#listStatement.
    def exitListStatement(self, ctx:EntryFilterParser.ListStatementContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#operator.
    def enterOperator(self, ctx:EntryFilterParser.OperatorContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#operator.
    def exitOperator(self, ctx:EntryFilterParser.OperatorContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#booleanOperator.
    def enterBooleanOperator(self, ctx:EntryFilterParser.BooleanOperatorContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#booleanOperator.
    def exitBooleanOperator(self, ctx:EntryFilterParser.BooleanOperatorContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#value.
    def enterValue(self, ctx:EntryFilterParser.ValueContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#value.
    def exitValue(self, ctx:EntryFilterParser.ValueContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#listValue.
    def enterListValue(self, ctx:EntryFilterParser.ListValueContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#listValue.
    def exitListValue(self, ctx:EntryFilterParser.ListValueContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#stringValue.
    def enterStringValue(self, ctx:EntryFilterParser.StringValueContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#stringValue.
    def exitStringValue(self, ctx:EntryFilterParser.StringValueContext):
        pass


    # Enter a parse tree produced by EntryFilterParser#numberValue.
    def enterNumberValue(self, ctx:EntryFilterParser.NumberValueContext):
        pass

    # Exit a parse tree produced by EntryFilterParser#numberValue.
    def exitNumberValue(self, ctx:EntryFilterParser.NumberValueContext):
        pass



del EntryFilterParser