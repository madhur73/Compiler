A demo script is provided to run the scanner on the included test files.
Run from this directory:

	python3 demo_tests.py
	
Or to give custom input through stdin:
	
	python3 demo_stdin.py
	
	"press ctrl + d to exit the input and ctrl + c to quit the program"

The module was tested on Python 3.6.7.

	- tests/
	  Contains demo source files, used by demo_tests.py.
	- token.py
	  Defines a Token class.
	- scanner.py
	  The interesting part.
	- demo_tests.py, demo_stdin.py
	  Demo scripts, as described above.
	- demo_tests_output.txt
	  Sample output from running demo_tests.py.
