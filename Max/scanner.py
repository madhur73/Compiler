import enum
import re
import string
    
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
    def __init__(self, type, string, file_offset, line, column):
        self.type = type
        self.string = string
        self.file_offset = file_offset
        self.line = line
        self.column = column
    
    def __str__(self):
        return f'{self.line}:{self.column} ({self.file_offset}) {self.type} "{self.string}"'

class Scanner:
    def __init__(self, source):
        self._s = source
        
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
        match = re.match("\*\*\*.*", self._s[self._b:]) # Note: the .* will not match newlines.
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
            if self._b >= len(self._s):
                return Token(TokenType.EOF, "", self._b, self._line, self._column)
            
            self._skip_whitespace()
            
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
                token = Token(token_type, token_string, self._b, self._line, self._column)
                self._advance_b(advancement)
                return token
            
            self._warn(f"Unrecognized character {self._s[self._b]}.")
            self._advance_b(1)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        n = self.next()
        if n.type == TokenType.EOF:
            raise StopIteration()
        else:
            return n

# To do: peek
# To do: file opening
# To do: error combination
# To do: test suites
# To do: documentation
