import bmc.scanner
import bmc.parse
from sys import stdin
print("Reading from standard input...")
scanner = bmc.scanner.Scanner(file=stdin, emit_comments=False)
bmc.parse.parse_report_errors(scanner)
