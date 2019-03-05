import re
import string
    
from token import *

# Each token type corresponds to a regular expression pattern.  Each pattern is
# wrapped as a group, and those groups are concatenated into one big mega-regex.
# The lexer attempts to match this mega-regex against the remaining input. The
# group that sucessfully matches, if there is one, corresponds to the next token.

_patterns = [
    (TokenType.COMMENT,         "\\*\\*\\*.*"),
    (TokenType.KW_ARRAY,        "array"),
    (TokenType.KW_TUPLE,        "tuple"),
    (TokenType.KW_LOCAL,        "local"),
    (TokenType.KW_GLOBAL,       "global"),
    (TokenType.KW_DEFUN,        "defun"),
    (TokenType.KW_END,          "end"),
    (TokenType.KW_WHILE,        "while"),
    (TokenType.KW_DO,           "do"),
    (TokenType.KW_IF,           "if"),
    (TokenType.KW_THEN,         "then"),
    (TokenType.KW_ELSIF,        "elsif"),
    (TokenType.KW_ELSE,         "else"),
    (TokenType.KW_FOREACH,      "foreach"),
    (TokenType.KW_IN,           "in"),
    (TokenType.RETURN,          "return"),
    (TokenType.PRINT,           "print"),
    (TokenType.OP_COMMA,        ","),
    (TokenType.SEMI,            ";"),
    (TokenType.LPAR,            "\\("),
    (TokenType.RPAR,            "\\)"),
    (TokenType.LBRAK,           "\\["),
    (TokenType.RBRAK,           "\\]"),
    (TokenType.OP_DOTDOT,       "\\.\\."),
    (TokenType.OP_DOT,          "\\."),
    (TokenType.INT_LIT,         "[0-9]+"),
    (TokenType.ID,              "[a-zA-Z_]+"),
    (TokenType.EXCHANGE,        "<->"),
    (TokenType.OP_LESSEQUAL,    "<="),
    (TokenType.OP_GREATEREQUAL, ">="),
    (TokenType.OP_LESS,         "<"),
    (TokenType.OP_GREATER,      ">"),
    (TokenType.OP_EQUAL,        "=="),
    (TokenType.OP_NOTEQUA,      "!="),
    (TokenType.ASSIGN,          "="),
    (TokenType.OP_PLUS,         "\\+"),
    (TokenType.OP_MINUS,        "-"),
    (TokenType.OP_MULT,         "\\*"),
    (TokenType.OP_DIV,          "/"),
]

_mega_regex = re.compile("|".join("("+p+")" for t, p in _patterns))

# Returns the token at the start of source[begin:] as a tuple (type, value),
# or (None, "") if there is no valid token there.
def _next_token(source, begin):
    match = _mega_regex.match(source, begin)
    if match:
        matched_group_index = match.lastindex - 1
        return (_patterns[matched_group_index][0], match[0])
    else:
        return None, ""
        

class Scanner:
    def __init__(self, *, string="", filepath=None, emit_comments=True):
        if filepath:
            with open(filepath) as file:
                string = file.read()
        
        self._s = string
        self._emit_comments = emit_comments
        
        # File offset to beginning of next token.
        self._b = 0
        
        # Human-readable location of self._b.  A newline character itself is on
        # the end of a line, not on the beginning of a new line.
        self._line = 1
        self._column = 1
    
    def _warn(self, message):
        print(f"{self._line}:{self._column} Warning: {message}")
    
    def _advance_b(self, amount):
        self._b += amount
        self._column += amount
    
    def _skip_whitespace(self):
        while self._b < len(self._s) and self._s[self._b] in string.whitespace:
            if self._s[self._b] == "\n":
                self._line += 1
                self._column = 0 # Will be advanced to 1 below.
            self._advance_b(1)
    
    def next(self):
        while True:
            self._skip_whitespace()
            
            if self._b >= len(self._s):
                return Token(TokenType.EOF, "", self._b, self._b, self._line, self._column)
            
            token_type, raw_value = _next_token(self._s, self._b)
            
            if token_type is None:
                self._warn(f'unrecognized character "{self._s[self._b]}".')
                self._advance_b(1)
                continue
            
            value = raw_value
            if token_type == TokenType.ID and len(raw_value) > 80:
                self._warn(f'identifier "{raw_value}" will be truncated to 80 characters.')
                value = raw_value[:80]
            elif token_type == TokenType.INT_LIT and int(raw_value) >= 2**31:
                self._warn(f'integer "{raw_value}" will be clamped to 2^31-1.')
                value = str(2**31 - 1)
            
            token = Token(token_type, value, self._b, self._b+len(raw_value), self._line, self._column)
            self._advance_b(len(raw_value))
            return token
    
    def peek(self):
        # Scan the next token, but then roll back the current position.
        b, line, column = self._b, self._line, self._column
        next = self.next()
        self._b, self._line, self._column = b, line, column
        return next
    
    def __iter__(self):
        return self
    
    def __next__(self):
        n = self.next()
        if n.type == TokenType.EOF:
            raise StopIteration()
        else:
            return n

# To do: file opening
# To do: error combination
# To do: test suites
# To do: documentation
