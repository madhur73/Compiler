from scanner import Scanner
from sys import stdin

s = Scanner(file=stdin)
for token in s:
	print(token)
