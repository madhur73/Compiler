

We're using Python. Everything up to the code generation is hand-written. Code generation uses llvmlite to output formatted and validated LLVM IR.
Following are DONE-

    1.The scanner
    2.The parser
    3.Code generation and semantic analysis are limited to:
        a.Printing.
        b.Global declarations of tuples.
        c.Assignment statements.

    4.Error recovery doesn't work. The compiler stops on the first error.
    5.In the global scope:
	    a.The complete set of tuple operations - declarations, assignments, exchanges(not confused with any)
	    b.Arithmetic
	    c.If-statements (including elsif, nesting, etc.)
	    d.While-loops
	    e.Statement-level semantic error recovery - if one statement is semantically invalid, we still check the ones that come after it

Following are NOT DONE(Incomplete) only Scanning and Pasrsing works:.

   1. arrays
   2. functions.

     
