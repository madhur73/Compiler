# Usage

To test the parser on stdin, run, from the root directory,

    python3 demo.py

To run all the included test files, run, from the root directory,

    python3 test_ast.py

# Contents

The interesting code is in the `bmc` directory (standing for Biyani-Marrone Compiler).  `parser.py` contains the new parser code.  `ast.py` defines classes for the abstract syntax tree that `parser.py` builds. `tests` contains example source code, used by `test_ast.py`.
