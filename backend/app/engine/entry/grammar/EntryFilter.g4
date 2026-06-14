grammar EntryFilter;

// ─── Parser Rules ─────────────────────────────────────────────────────────────

expression
    : unaryStatement (booleanOperator unaryStatement)*
    ;

unaryStatement
    : operator value
    | LEFTPAREN expression RIGHTPAREN
    | listStatement
    ;

listStatement
    : IN listValue
    | NOTIN listValue
    ;
operator
    : EQUAL
    | NOTEQUAL
    | GREATERTHAN
    | LESSTHAN
    | GREATEREQUAL
    | LESSEQUAL
    | FUZZY
    ;

booleanOperator
    : AND
    | OR
    ;

value
    : stringValue
    | numberValue
    ;

listValue
    : LEFTBRAKET value (COMMA value)* RIGHTBRAKET
    ;
stringValue
    : STRING
    ;


numberValue
    : INTEGER
    | DOUBLE
    | SCIENTIFIC
    ;

// ─── Lexer Rules ──────────────────────────────────────────────────────────────

// Operators
EQUAL         : '='  ;
NOTEQUAL      : '!=' ;
GREATEREQUAL  : '>=' ;
LESSEQUAL     : '<=' ;
GREATERTHAN   : '>'  ;
LESSTHAN      : '<'  ;
FUZZY         : '~'  ;
IN            : ':in' ;
NOTIN         : '!in';

// Boolean
AND           : 'and' ;
OR            : 'or'  ;

// Delimiters
LEFTBRAKET    : '[' ;
RIGHTBRAKET   : ']' ;
LEFTPAREN  : '(' ;
RIGHTPAREN : ')' ;
COMMA         : ',' ;

// Values
INTEGER       : '-'? [0-9]+ ;
DOUBLE        : '-'? [0-9]+ '.' [0-9]+ ;
SCIENTIFIC    : '-'? [0-9]+ ('.' [0-9]+)? [eE] [+-]? [0-9]+ ;

// String: unquoted — any non-whitespace, non-bracket, non-comma text
STRING : [a-zA-Z0-9] [a-zA-Z0-9_\-.]* ;

// Skip whitespace
WS            : [ \t\r\n]+ -> skip ;