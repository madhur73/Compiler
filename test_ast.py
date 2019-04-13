from bmc.ast import *
from bmc import scanner
from bmc.token import TokenType
from bmc.parse import *

print("Welcome to...\n")
print("-------\n|B|M|C\n--------\nversion1.0.0")

for i in range(7):
	
	print("-------------------------test case "+str(i)+" -------------------------")
	file = open("tests/p2test"+str(i)+".txt","r") 
	print(file.read())
	print("------------------------- AST ---------------------------------")

	s = scanner.Scanner(emit_comments = False,filepath="tests/p2test"+str(i)+".txt")
	parse_report_errors(s)
		
