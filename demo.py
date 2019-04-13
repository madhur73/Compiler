import bmc.scanner
import bmc.parse
from sys import stdin
print("Reading from standard input...")
scanner = bmc.scanner.Scanner(file=stdin, emit_comments=False)
try:
	ast = bmc.parse.parse_program(scanner)
	print("Success!")
	print(ast)
except bmc.parse.ParseError as error:
	print("Error.")
	print("Got", scanner.peek())
	print("But expected " + " or ".join(str(t) for t in error.expected))
