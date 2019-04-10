#define a tken
tokenList = ['a','b','c','d','f','g']
#hardcoded the grammar
grammar = {}
grammar["S"] = [['c','A','d'],['f','g']]
grammar["A"] = [['a','b'],['a']]

""""
tokenList = ['+',"*","(",")","id"]
grammar = {}
grammar["E"] = [['T','G']]
grammar["G"] = [['+','T','G'],["#"]]
grammar["T"] = [['F','H']]
grammar["H"] = [['*','F','H'],["#"]]
grammar["F"] = [['(',"E",")"],["id"]]
"""
inputString = "cad"

#check wheher the character is terminala or not
def isTerminal(token):
	for i in range(0,len(tokenList)):
		if(tokenList[i] == token):
			return True
	return False

def RDP(nonterminal, inputptr):
	#for each production of a Non-Terminal
	#match holding 
	for rule in grammar[nonterminal]:
		current  = inputptr
		match = len(rule)
		#for each character ina a production
		for i in range(0,len(rule)):
			if(rule[i] == "#"):
				print("epsilon",current)
				match-=1
				break	
			if(not isTerminal(rule[i])):	
				current1 = RDP(rule[i],current)
				match-=1
				current = current1
			elif(rule[i] == inputString[current]):
				print(rule[i],"matched with  {} match ".format(inputString[current]),match)
				current+=1
				match-=1
			else:
				print("error",match,inputString[current],rule)
				break
			if(match == 0 and nonterminal!="S"):
				print("match end----",match,rule)
				return current
		if(match ==0 and nonterminal == "S"):
			print("parsed sucess")
			return -100;
	print("match end2",match,current,rule)
	return current


""""	
def S(inputptr):
	for rule in Start:
		current  = inputptr
		match = len(rule)
		for i in range(0,len(rule)):	
			if(not isTerminal(rule[i])):	
				current1 = eval(rule[i]+"({})".format(current))
				if(current1 != current):
					print(rule[i],"matched with rule {}".format(inputString[current]))
					match-=1
				current = current1
			elif(rule[i] == inputString[current]):
				print(rule[i],"matched with rule {}".format(inputString[current]))
				current+=1
				match-=1
			else:
				print("error")
	if(match == 0):
		print("parse complete")
	else:
		print("String not matched")
def A(inputptr):
	for rule in End:
		current  = inputptr
		match = len(rule)
		for i in range(0,len(rule)):	
			if(not isTerminal(rule[i])):
				print(rule[i],"matched with rule {}".format(inputString[current]))
				current1 = eval(rule[i]+"({})".format(current))
				if(current1 != current):
					print(match,current1,current)
					match-=1
				current = current1
			elif(rule[i] == inputString[current]):
				print(rule[i],"matched with rule {}".format(inputString[current]))
				current+=1
				match-=1
			else:
				print("error")
		if(match == 0):
			return current
	return current
"""
result = RDP("S",0)
#print(result,"result")
if(result ==-100):
	print("string parsable by grammar")
else:
	print("string NOT ** parsable by grammar")
