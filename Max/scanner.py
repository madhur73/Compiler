import re
import string
    
from token import *

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
    
    def _scan_comment(self):
        match = re.match(r"\*\*\*.*", self._s[self._b:]) # Note the . will not match newlines.
        if match:
            return TokenType.COMMENT, match[0], len(match[0])
        else:
            return None
    
    def _scan_operator(self):
        T = TokenType
        operators = [ # Order matters, e.g. OP_DOTDOT is preferred over two OP_DOTs.
            ("..",  T.OP_DOTDOT),
            (".",   T.OP_DOT),
            ("[",   T.LBRAK),
            ("]",   T.RBRAK),
            ("(",   T.LPAR),
            (")",   T.RPAR),
            (";",   T.SEMI),
            (",",   T.OP_COMMA),
            ("==",  T.OP_EQUAL),
            ("!=",  T.OP_NOTEQUA),
            ("=",   T.ASSIGN),
            ("<->", T.EXCHANGE),
            ("<=",  T.OP_LESSEQUAL),
            ("<",   T.OP_LESS),
            (">=",  T.OP_GREATEREQUAL),
            (">",   T.OP_GREATER),
            ("+",   T.OP_PLUS),
            ("-",   T.OP_MINUS),
            ("*",   T.OP_MULT),
            ("/",   T.OP_DIV)
        ]    
        for string, token_type in operators:
            if self._s.startswith(string, self._b):
                return token_type, string, len(string)
        return None
    
    def _scan_id_or_keyword(self):
        keywords = {
            "array":   TokenType.KW_ARRAY,
            "tuple":   TokenType.KW_TUPLE,
            "local":   TokenType.KW_LOCAL,
            "global":  TokenType.KW_GLOBAL,
            "defun":   TokenType.KW_DEFUN,
            "end":     TokenType.KW_END,
            "while":   TokenType.KW_WHILE,
            "do":      TokenType.KW_DO,
            "if":      TokenType.KW_IF,
            "then":    TokenType.KW_THEN,
            "elsif":   TokenType.KW_ELSIF,
            "else":    TokenType.KW_ELSE,
            "foreach": TokenType.KW_FOREACH,
            "in":      TokenType.KW_IN,
            "return":  TokenType.RETURN,
            "print":   TokenType.PRINT
        }
        match = re.match("[a-zA-Z_]+", self._s[self._b:])
        if match:
            string = match[0]
            token_type = keywords.get(string, TokenType.ID)
            if len(string) > 80:
                self._warn(f'identifier "{string}" will be truncated to 80 characters.')
            return token_type, string[:80], len(string)
        return None
    
    def _scan_integer_literal(self):
        match = re.match("[0-9]+", self._s[self._b:])
        if match:
            string = match[0]
            if int(string) >= 2**31:
                self._warn(f'integer "{string}" will be clamped to 2^31.')
                string = str(2**31)
            return TokenType.INT_LIT, string, len(match[0])
        return None
    
    def next(self):
        while True:
            self._skip_whitespace()
            
            if self._b >= len(self._s):
                return Token(TokenType.EOF, "", self._b, self._b, self._line, self._column)
            
            scan_tasks = [
                self._scan_comment,
                self._scan_operator,
                self._scan_id_or_keyword,
                self._scan_integer_literal
            ]
            
            for scan_task in scan_tasks:
                scan_result = scan_task()
                if not scan_result: continue
                token_type, token_string, advancement = scan_result
                if (not self._emit_comments) and (token_type == TokenType.COMMENT):
                    continue
                token = Token(token_type, token_string, self._b, self._b+advancement, self._line, self._column)
                self._advance_b(advancement)
                return token
            
            self._warn(f'unrecognized character "{self._s[self._b]}".')
            self._advance_b(1)
    
    def peek(self):
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
