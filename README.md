# Usage

To test the type checker on stdin, run, from the root directory,

    python3 demo.py

To run all the included test files, run, from the root directory,

    python3 test_ast.py

# Contents

The interesting code is in the `bmc` directory (standing for Biyani-Marrone Compiler).  `ast.py` contains the type checking code, with utility function support from `type_check.py`.

# Functionality

A very limited set of global statements sort of works.  You should be able to assign between global variables of different sizes, and it will detect undeclared variables.  All function calls are assumed to return a single int.
