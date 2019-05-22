We're using Python. Everything up to the code generation is hand-written. Code generation uses llvmlite to output formatted and validated LLVM IR.

The following are done:

* The scanner, and token output
* The parser, and AST output, with the limitation that it can only handle one error at a time

The code generation and semantic analysis stage is incomplete:

* Print statements for integers and tuples are supported.
* Tuple assignments and exchanges (from integers, or other tuples, or some combination) is supported.
* Arithmetic is supported.
* If-statements and conditionals are supported, including elsif, nesting, etc.
* While-loops are supported.
* Foreach-loops are entirely unsupported.
* Arrays are entirely unsupported.  There is some code for setting up the stack space for array declarations, but not enough to be functional.  What is missing is the semantic analysis part, i.e., knowing that `global a; array a[1..2];` means that `a` is an array and not a tuple when it is referred to in subsequent expressions.
* Functions (and therefore local declarations and return statements) are entirely unsupported.
* Both code generation and semantic analysis (making sure variables are not used before they are declared, etc.) works for what is supported, as described above.
* Except for syntax errors, we try to recover from errors in the input source code.  All errors are printed in lexical order with a helpful message.  Certain errors are printed without location information.

See `example.boris` for a fully supported sample program.
