# Usage

To test the parser on stdin, run, from the root directory,

    python3 demo.py

To run all the included test files, run, from the root directory,

    python3 test_ast.py

# Contents

The interesting code is in the `bmc` directory (standing for Biyani-Marrone Compiler).  `parser.py` contains the new parser code.  `ast.py` defines classes for the abstract syntax tree that `parser.py` builds. `tests` contains example source code, used by `test_ast.py`.

# Functionality

The parser tries to give useful diagnostics: what was expected versus what it actually found.  It doesn't yet attempt any form of error recovery.  When error recovery is added, it will likely be through the `parse_repeating()` function, which normally returns a list.  Items in the list where the parser failed could simply be skipped, keeping the structure of the AST unchanged.

There is a known parsing bug shown in test case 5: statements like a=a.0; are incorrectly rejected.

# Example

Here is the result of parsing `array a[234..123] a=a*a;`:

    Program
      parts = [
        ArrayDeclaration
          identifier = 1:7 (6-7) TokenType.ID "a"
          range = Range
            begin_expression = IntegerLiteralExpression
              token = 1:10 (9-12) TokenType.INT_LIT "234"
            end_expression = IntegerLiteralExpression
              token = 1:15 (14-17) TokenType.INT_LIT "123"
          index_identifier = 1:20 (19-20) TokenType.ID "a"
          index_expression = MultiplyExpression
            left = IdentifierExpression
              identifier_token = 1:24 (23-24) TokenType.ID "a"
            right = IdentifierExpression
              identifier_token = 1:26 (25-26) TokenType.ID "a"
      ]

Where `[...]` represents a flat list, and `x = ...` represents a child node called `x`.
