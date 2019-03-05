import enum

TokenType = enum.Enum("TokenType", """
    KW_ARRAY
    ID
    OP_DOTDOT
    LBRAK
    RBRAK
    SEMI
    KW_TUPLE
    KW_LOCAL
    KW_GLOBAL
    KW_DEFUN
    LPAR
    RPAR
    OP_COMMA
    KW_END
    KW_WHILE
    KW_DO
    KW_IF
    KW_THEN
    KW_ELSIF
    KW_ELSE
    KW_FOREACH
    KW_IN
    OP_DOT
    INT_LIT
    RETURN
    PRINT
    ASSIGN
    EXCHANGE
    OP_LESS
    OP_GREATER
    OP_LESSEQUAL
    OP_GREATEREQUAL
    OP_EQUAL
    OP_NOTEQUA
    OP_PLUS
    OP_MINUS
    OP_MULT
    OP_DIV
    COMMENT
    EOF
""") # Note no OP_UMINUS.

class Token:
    def __init__(self, type, string, begin, end, line, column):
        self.type = type
        self.string = string
        self.begin = begin
        self.end = end
        self.line = line
        self.column = column
    
    def __str__(self):
        return f'{self.line}:{self.column} ({self.begin}-{self.end}) {self.type} "{self.string}"'
