import re
import string
    
from bmc.token import *

# Each token type corresponds to a regular expression pattern.  Each pattern is
# wrapped as a group, and those groups are concatenated into one big mega-regex.
# The scanner attempts to match this mega-regex against the remaining input. The
# group that sucessfully matches, if there is one, corresponds to the next
# token.  Ordering is significant: longer operators like >= should appear before
# shorter operators like >, so they take precedence.
_patterns = [
    (TokenType.COMMENT,         r"\*\*\*.*"),
    (TokenType.OP_COMMA,        r","),
    (TokenType.SEMI,            r";"),
    (TokenType.LPAR,            r"\("),
    (TokenType.RPAR,            r"\)"),
    (TokenType.LBRAK,           r"\["),
    (TokenType.RBRAK,           r"\]"),
    (TokenType.OP_DOTDOT,       r"\.\."),
    (TokenType.OP_DOT,          r"\."),
    (TokenType.INT_LIT,         r"[0-9]+"),
    (TokenType.ID,              r"[a-zA-Z_]+"),
    (TokenType.EXCHANGE,        r"<->"),
    (TokenType.OP_LESSEQUAL,    r"<="),
    (TokenType.OP_GREATEREQUAL, r">="),
    (TokenType.OP_LESS,         r"<"),
    (TokenType.OP_GREATER,      r">"),
    (TokenType.OP_EQUAL,        r"=="),
    (TokenType.OP_NOTEQUA,      r"!="),
    (TokenType.ASSIGN,          r"="),
    (TokenType.OP_PLUS,         r"\+"),
    (TokenType.OP_MINUS,        r"-"),
    (TokenType.OP_MULT,         r"\*"),
    (TokenType.OP_DIV,          r"/"),
]

# Keywords are just IDs with special values.  They can't be directly included
# in the mega-regex because they can interfere with scanning IDs.
_keywords = {
    "array":   TokenType.KW_ARRAY,
    "defun":   TokenType.KW_DEFUN,
    "do":      TokenType.KW_DO,
    "else":    TokenType.KW_ELSE,
    "elsif":   TokenType.KW_ELSIF,
    "end":     TokenType.KW_END,
    "foreach": TokenType.KW_FOREACH,
    "for":     TokenType.KW_FOR,
    "global":  TokenType.KW_GLOBAL,
    "if":      TokenType.KW_IF,
    "in":      TokenType.KW_IN,
    "local":   TokenType.KW_LOCAL,
    "print":   TokenType.PRINT,
    "return":  TokenType.RETURN,
    "then":    TokenType.KW_THEN,
    "tuple":   TokenType.KW_TUPLE,
    "while":   TokenType.KW_WHILE,
}

_mega_regex = re.compile("|".join("("+p+")" for t, p in _patterns))

# Returns the token at the start of source[begin:] as a tuple (type, value),
# or (None, "") if there is no valid token there.
def _next_token(source, begin):
    # Technique inspired by an example from the Python regex docs:
    # https://docs.python.org/3/library/re.html#writing-a-tokenizer
    match = _mega_regex.match(source, begin)
    if match:
        matched_group_index = match.lastindex - 1
        token_type, _ = _patterns[matched_group_index]
        value = match.group()
        if token_type == TokenType.ID:
            token_type = _keywords.get(value, TokenType.ID)
        return token_type, value
    else:
        return None, ""

class Scanner:
    def __init__(self, *, string="", filepath=None, file=None, emit_comments=False):
        """Initializes a Scanner.
        
        The full source must be provided as either a single string, a file, or a path to a file.
        If a file is provided, it will not be closed.
        
        Comment tokens will be included in the output stream only if emit_comments is true.
        
        Non-ASCII is accepted in comments, but rejected everywhere else.
        """
        
        if filepath:
            with open(filepath) as file:
                string = file.read()
        elif file:
            string = file.read()
        
        self._s = string
        self._emit_comments = emit_comments
        
        # File offset to beginning of next token.
        self._b = 0
        
        # Human-readable location of self._b.  A newline character itself is on
        # the end of a line, not on the beginning of a new line.
        self._line = 1
        self._column = 1
    
    # Print a warning with a position tag from the current position with a length of error_length.
    def _warn(self, message, error_length):
        print("{}:{}-{}:{} Warning: {}".format(self._line, self._column, self._line, self._column+error_length, message))
    
    def _advance_b(self, amount):
        self._b += amount
        self._column += amount
    
    # Skip over whitespace, including newlines, and advance the file offset,
    # line counter and column counter as necessary.
    def _skip_whitespace(self):
        while self._b < len(self._s) and self._s[self._b] in string.whitespace:
            if self._s[self._b] == "\n":
                self._line += 1
                self._column = 0 # Will be advanced to 1 below.
            self._advance_b(1)
    
    def next(self):
        """Consumes and returns the next token, or an EOF token if there are none left."""
        
        while True:
            self._skip_whitespace()
            
            if self._b >= len(self._s):
                return Token(TokenType.EOF, "", self._b, self._b, self._line, self._column)
            
            token_type, raw_value = _next_token(self._s, self._b)
            
            if token_type is None:
                self._warn('unrecognized character "{}".'.format(self._s[self._b]), 1)
                self._advance_b(1)
                continue
            
            value = raw_value
            if token_type == TokenType.ID and len(raw_value) > 80:
                self._warn('identifier "{}" will be truncated to 80 characters.'.format(raw_value), len(raw_value))
                value = raw_value[:80]
            elif token_type == TokenType.INT_LIT and int(raw_value) >= 2**31:
                self._warn('integer "{}" will be clamped to 2^31-1.'.format(raw_value), len(raw_value))
                value = str(2**31 - 1)
            
            token = Token(token_type, value, self._b, self._b+len(raw_value), self._line, self._column)
            self._advance_b(len(raw_value))
            
            if token_type == TokenType.COMMENT and not self._emit_comments:
                continue
            else:
                return token
    
    def peek(self):
        """Returns the next token, as in Scanner.next(), but without consuming it."""
        # Scan the next token, but then roll back the current position.
        b, line, column = self._b, self._line, self._column
        next = self.next()
        self._b, self._line, self._column = b, line, column
        return next
    
    def rollback(next_token):
        """Returns the scanner to a state where scanner.peek() == next_token."""
        self._b = next_token.begin
        self._line = next_token.line
        self._column = next_token.column
    
    def __iter__(self):
        return self
    
    def __next__(self):
        """Allows for iteration over all the tokens in the source, as if by next(), except that an EOF token is not included."""
        n = self.next()
        if n.type == TokenType.EOF:
            raise StopIteration()
        else:
            return n
