import bmc.scanner
import bmc.parse
from sys import stdin
print("Reading from standard input...")
scanner = bmc.scanner.Scanner(file=stdin, emit_comments=False)
for token in scanner:
    print(token)
