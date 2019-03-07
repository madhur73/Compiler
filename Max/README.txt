A demo script is provided to run the scanner on the included test files.
Run from this directory:

	python3 demo_tests.py
	
Or to give custom input through stdin:
	
	python3 demo_stdin.py

The module was tested on Python 3.6.7.

	- tests/
	  Contains demo source files, used by demo.py.
	- token.py
	  Defines a Token class.
	- scanner.py
	  The interesting part.

The initial implementation used a backtracking approach, trying to match each token type against the remainder of the string until one of them succeeded.  The current implementation effectively does the same thing, but this logic is embedded in a single large regex.  (One of the groups in the regex will match; the token type is determined by which group that is.)  We found that this approach is both more concise and faster, presumably because it gives more of the work to the optimized Python regex engine.
