import bmc.scanner
import bmc.parse
from sys import stdin
print("Reading from standard input...")
scanner = bmc.scanner.Scanner(file=stdin, emit_comments=False)
ast = bmc.parse.parse_report_errors(scanner)
print(ast)
ast.type_check()
print("Done type check")
