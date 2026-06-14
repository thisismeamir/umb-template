# Generated from EntryFilter.g4 by ANTLR 4.11.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,21,67,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,1,0,1,0,1,0,1,0,5,0,23,8,0,10,0,12,0,26,9,0,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,36,8,1,1,2,1,2,1,2,1,2,3,2,42,
        8,2,1,3,1,3,1,4,1,4,1,5,1,5,3,5,50,8,5,1,6,1,6,1,6,1,6,5,6,56,8,
        6,10,6,12,6,59,9,6,1,6,1,6,1,7,1,7,1,8,1,8,1,8,0,0,9,0,2,4,6,8,10,
        12,14,16,0,3,1,0,1,7,1,0,10,11,1,0,17,19,63,0,18,1,0,0,0,2,35,1,
        0,0,0,4,41,1,0,0,0,6,43,1,0,0,0,8,45,1,0,0,0,10,49,1,0,0,0,12,51,
        1,0,0,0,14,62,1,0,0,0,16,64,1,0,0,0,18,24,3,2,1,0,19,20,3,8,4,0,
        20,21,3,2,1,0,21,23,1,0,0,0,22,19,1,0,0,0,23,26,1,0,0,0,24,22,1,
        0,0,0,24,25,1,0,0,0,25,1,1,0,0,0,26,24,1,0,0,0,27,28,3,6,3,0,28,
        29,3,10,5,0,29,36,1,0,0,0,30,31,5,14,0,0,31,32,3,0,0,0,32,33,5,15,
        0,0,33,36,1,0,0,0,34,36,3,4,2,0,35,27,1,0,0,0,35,30,1,0,0,0,35,34,
        1,0,0,0,36,3,1,0,0,0,37,38,5,8,0,0,38,42,3,12,6,0,39,40,5,9,0,0,
        40,42,3,12,6,0,41,37,1,0,0,0,41,39,1,0,0,0,42,5,1,0,0,0,43,44,7,
        0,0,0,44,7,1,0,0,0,45,46,7,1,0,0,46,9,1,0,0,0,47,50,3,14,7,0,48,
        50,3,16,8,0,49,47,1,0,0,0,49,48,1,0,0,0,50,11,1,0,0,0,51,52,5,12,
        0,0,52,57,3,10,5,0,53,54,5,16,0,0,54,56,3,10,5,0,55,53,1,0,0,0,56,
        59,1,0,0,0,57,55,1,0,0,0,57,58,1,0,0,0,58,60,1,0,0,0,59,57,1,0,0,
        0,60,61,5,13,0,0,61,13,1,0,0,0,62,63,5,20,0,0,63,15,1,0,0,0,64,65,
        7,2,0,0,65,17,1,0,0,0,5,24,35,41,49,57
    ]

class EntryFilterParser ( Parser ):

    grammarFileName = "EntryFilter.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'='", "'!='", "'>='", "'<='", "'>'", 
                     "'<'", "'~'", "':in'", "'!in'", "'and'", "'or'", "'['", 
                     "']'", "'('", "')'", "','" ]

    symbolicNames = [ "<INVALID>", "EQUAL", "NOTEQUAL", "GREATEREQUAL", 
                      "LESSEQUAL", "GREATERTHAN", "LESSTHAN", "FUZZY", "IN", 
                      "NOTIN", "AND", "OR", "LEFTBRAKET", "RIGHTBRAKET", 
                      "LEFTPAREN", "RIGHTPAREN", "COMMA", "INTEGER", "DOUBLE", 
                      "SCIENTIFIC", "STRING", "WS" ]

    RULE_expression = 0
    RULE_unaryStatement = 1
    RULE_listStatement = 2
    RULE_operator = 3
    RULE_booleanOperator = 4
    RULE_value = 5
    RULE_listValue = 6
    RULE_stringValue = 7
    RULE_numberValue = 8

    ruleNames =  [ "expression", "unaryStatement", "listStatement", "operator", 
                   "booleanOperator", "value", "listValue", "stringValue", 
                   "numberValue" ]

    EOF = Token.EOF
    EQUAL=1
    NOTEQUAL=2
    GREATEREQUAL=3
    LESSEQUAL=4
    GREATERTHAN=5
    LESSTHAN=6
    FUZZY=7
    IN=8
    NOTIN=9
    AND=10
    OR=11
    LEFTBRAKET=12
    RIGHTBRAKET=13
    LEFTPAREN=14
    RIGHTPAREN=15
    COMMA=16
    INTEGER=17
    DOUBLE=18
    SCIENTIFIC=19
    STRING=20
    WS=21

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.11.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unaryStatement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(EntryFilterParser.UnaryStatementContext)
            else:
                return self.getTypedRuleContext(EntryFilterParser.UnaryStatementContext,i)


        def booleanOperator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(EntryFilterParser.BooleanOperatorContext)
            else:
                return self.getTypedRuleContext(EntryFilterParser.BooleanOperatorContext,i)


        def getRuleIndex(self):
            return EntryFilterParser.RULE_expression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = EntryFilterParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 18
            self.unaryStatement()
            self.state = 24
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==10 or _la==11:
                self.state = 19
                self.booleanOperator()
                self.state = 20
                self.unaryStatement()
                self.state = 26
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UnaryStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def operator(self):
            return self.getTypedRuleContext(EntryFilterParser.OperatorContext,0)


        def value(self):
            return self.getTypedRuleContext(EntryFilterParser.ValueContext,0)


        def LEFTPAREN(self):
            return self.getToken(EntryFilterParser.LEFTPAREN, 0)

        def expression(self):
            return self.getTypedRuleContext(EntryFilterParser.ExpressionContext,0)


        def RIGHTPAREN(self):
            return self.getToken(EntryFilterParser.RIGHTPAREN, 0)

        def listStatement(self):
            return self.getTypedRuleContext(EntryFilterParser.ListStatementContext,0)


        def getRuleIndex(self):
            return EntryFilterParser.RULE_unaryStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUnaryStatement" ):
                listener.enterUnaryStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUnaryStatement" ):
                listener.exitUnaryStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnaryStatement" ):
                return visitor.visitUnaryStatement(self)
            else:
                return visitor.visitChildren(self)




    def unaryStatement(self):

        localctx = EntryFilterParser.UnaryStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_unaryStatement)
        try:
            self.state = 35
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1, 2, 3, 4, 5, 6, 7]:
                self.enterOuterAlt(localctx, 1)
                self.state = 27
                self.operator()
                self.state = 28
                self.value()
                pass
            elif token in [14]:
                self.enterOuterAlt(localctx, 2)
                self.state = 30
                self.match(EntryFilterParser.LEFTPAREN)
                self.state = 31
                self.expression()
                self.state = 32
                self.match(EntryFilterParser.RIGHTPAREN)
                pass
            elif token in [8, 9]:
                self.enterOuterAlt(localctx, 3)
                self.state = 34
                self.listStatement()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IN(self):
            return self.getToken(EntryFilterParser.IN, 0)

        def listValue(self):
            return self.getTypedRuleContext(EntryFilterParser.ListValueContext,0)


        def NOTIN(self):
            return self.getToken(EntryFilterParser.NOTIN, 0)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_listStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterListStatement" ):
                listener.enterListStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitListStatement" ):
                listener.exitListStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitListStatement" ):
                return visitor.visitListStatement(self)
            else:
                return visitor.visitChildren(self)




    def listStatement(self):

        localctx = EntryFilterParser.ListStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_listStatement)
        try:
            self.state = 41
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [8]:
                self.enterOuterAlt(localctx, 1)
                self.state = 37
                self.match(EntryFilterParser.IN)
                self.state = 38
                self.listValue()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 2)
                self.state = 39
                self.match(EntryFilterParser.NOTIN)
                self.state = 40
                self.listValue()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OperatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EQUAL(self):
            return self.getToken(EntryFilterParser.EQUAL, 0)

        def NOTEQUAL(self):
            return self.getToken(EntryFilterParser.NOTEQUAL, 0)

        def GREATERTHAN(self):
            return self.getToken(EntryFilterParser.GREATERTHAN, 0)

        def LESSTHAN(self):
            return self.getToken(EntryFilterParser.LESSTHAN, 0)

        def GREATEREQUAL(self):
            return self.getToken(EntryFilterParser.GREATEREQUAL, 0)

        def LESSEQUAL(self):
            return self.getToken(EntryFilterParser.LESSEQUAL, 0)

        def FUZZY(self):
            return self.getToken(EntryFilterParser.FUZZY, 0)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_operator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOperator" ):
                listener.enterOperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOperator" ):
                listener.exitOperator(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOperator" ):
                return visitor.visitOperator(self)
            else:
                return visitor.visitChildren(self)




    def operator(self):

        localctx = EntryFilterParser.OperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_operator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            _la = self._input.LA(1)
            if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 254) != 0):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BooleanOperatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def AND(self):
            return self.getToken(EntryFilterParser.AND, 0)

        def OR(self):
            return self.getToken(EntryFilterParser.OR, 0)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_booleanOperator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBooleanOperator" ):
                listener.enterBooleanOperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBooleanOperator" ):
                listener.exitBooleanOperator(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBooleanOperator" ):
                return visitor.visitBooleanOperator(self)
            else:
                return visitor.visitChildren(self)




    def booleanOperator(self):

        localctx = EntryFilterParser.BooleanOperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_booleanOperator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 45
            _la = self._input.LA(1)
            if not(_la==10 or _la==11):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def stringValue(self):
            return self.getTypedRuleContext(EntryFilterParser.StringValueContext,0)


        def numberValue(self):
            return self.getTypedRuleContext(EntryFilterParser.NumberValueContext,0)


        def getRuleIndex(self):
            return EntryFilterParser.RULE_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterValue" ):
                listener.enterValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitValue" ):
                listener.exitValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitValue" ):
                return visitor.visitValue(self)
            else:
                return visitor.visitChildren(self)




    def value(self):

        localctx = EntryFilterParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_value)
        try:
            self.state = 49
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [20]:
                self.enterOuterAlt(localctx, 1)
                self.state = 47
                self.stringValue()
                pass
            elif token in [17, 18, 19]:
                self.enterOuterAlt(localctx, 2)
                self.state = 48
                self.numberValue()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LEFTBRAKET(self):
            return self.getToken(EntryFilterParser.LEFTBRAKET, 0)

        def value(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(EntryFilterParser.ValueContext)
            else:
                return self.getTypedRuleContext(EntryFilterParser.ValueContext,i)


        def RIGHTBRAKET(self):
            return self.getToken(EntryFilterParser.RIGHTBRAKET, 0)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(EntryFilterParser.COMMA)
            else:
                return self.getToken(EntryFilterParser.COMMA, i)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_listValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterListValue" ):
                listener.enterListValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitListValue" ):
                listener.exitListValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitListValue" ):
                return visitor.visitListValue(self)
            else:
                return visitor.visitChildren(self)




    def listValue(self):

        localctx = EntryFilterParser.ListValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_listValue)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 51
            self.match(EntryFilterParser.LEFTBRAKET)
            self.state = 52
            self.value()
            self.state = 57
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==16:
                self.state = 53
                self.match(EntryFilterParser.COMMA)
                self.state = 54
                self.value()
                self.state = 59
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 60
            self.match(EntryFilterParser.RIGHTBRAKET)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StringValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(EntryFilterParser.STRING, 0)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_stringValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStringValue" ):
                listener.enterStringValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStringValue" ):
                listener.exitStringValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStringValue" ):
                return visitor.visitStringValue(self)
            else:
                return visitor.visitChildren(self)




    def stringValue(self):

        localctx = EntryFilterParser.StringValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_stringValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 62
            self.match(EntryFilterParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTEGER(self):
            return self.getToken(EntryFilterParser.INTEGER, 0)

        def DOUBLE(self):
            return self.getToken(EntryFilterParser.DOUBLE, 0)

        def SCIENTIFIC(self):
            return self.getToken(EntryFilterParser.SCIENTIFIC, 0)

        def getRuleIndex(self):
            return EntryFilterParser.RULE_numberValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumberValue" ):
                listener.enterNumberValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumberValue" ):
                listener.exitNumberValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumberValue" ):
                return visitor.visitNumberValue(self)
            else:
                return visitor.visitChildren(self)




    def numberValue(self):

        localctx = EntryFilterParser.NumberValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_numberValue)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 64
            _la = self._input.LA(1)
            if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 917504) != 0):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





