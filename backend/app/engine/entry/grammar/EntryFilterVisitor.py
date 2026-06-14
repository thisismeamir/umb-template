# Generated from EntryFilter.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .EntryFilterParser import EntryFilterParser
else:
    from EntryFilterParser import EntryFilterParser

# This class defines a complete generic visitor for a parse tree produced by EntryFilterParser.

class EntryFilterVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by EntryFilterParser#expression.
    def visitExpression(self, ctx:EntryFilterParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#unaryStatement.
    def visitUnaryStatement(self, ctx:EntryFilterParser.UnaryStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#listStatement.
    def visitListStatement(self, ctx:EntryFilterParser.ListStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#operator.
    def visitOperator(self, ctx:EntryFilterParser.OperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#booleanOperator.
    def visitBooleanOperator(self, ctx:EntryFilterParser.BooleanOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#value.
    def visitValue(self, ctx:EntryFilterParser.ValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#listValue.
    def visitListValue(self, ctx:EntryFilterParser.ListValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#stringValue.
    def visitStringValue(self, ctx:EntryFilterParser.StringValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by EntryFilterParser#numberValue.
    def visitNumberValue(self, ctx:EntryFilterParser.NumberValueContext):
        return self.visitChildren(ctx)



del EntryFilterParser