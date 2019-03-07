from scanner import Scanner
from sys import stdin

test_files = [
	"tests/test1_all_tokens.txt",
	"tests/test2_garbage.txt",
	"tests/test3_outline.txt",
	"tests/test4_token_in_garbage.txt",
	"tests/test5_id_or_keyword.txt",
	"tests/test6_comments.txt",
	"tests/test7_tricky_operators.txt"
]

for test_file in test_files:
	
	print(test_file)
	print("=======================")
	print()
	
	s = Scanner(filepath=test_file, emit_comments=True)
	
	print("First token peeked:")
	print(s.peek())
	print()
	
	count = 0
	print("All tokens: (line:col (begin-end) TYPE \"value\")")
	for token in s:
		# Scanner objects are iterable.  This is equivalent to calling s.next() in a loop.
		# Errors will be printed to stdout.
		print(token)
		count += 1
	print("Done.  Scanned", count, "tokens.")
	
	print()
	print()
