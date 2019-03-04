import re
from token import token as tk

symTbl = {}
keyword ={"array":"KW_ARRAY" , 
	"tuple":"KW_TUPLE",
	"local":"KW_LOCAL" ,
	"global":"KW_GLOBAL",
	"defun":"KW_DEFUN","end":"KW_END",
	"while":"KW_WHILE",
	"do":"KW_DO" ,
	"if":"KW_IF" ,
	"then":"KW_THEN" ,
	"elsif":"KW_ELSIF" ,
	"else":"KW_ELSE",
	"foreach":"KW_FOREACH",
	"in":"KW_IN",}
char = {"[":"LBRAK",
	"]":"RBRAK" ,
	 ";":"SEMI",
	 "(":"LPAR" ,
	 ")":"RPAR"
	}
operators = {
	"..":"OP_DOTDOT",
	",":"OP_COMMA",
	".":"OP_DOT",
	"<":"OP_LESS" ,
	">":"OP_GREATER" ,
	"<=":"OP_LESSEQUAL" ,
	 ">=":"OP_GREATEREQUAL",
	"==":"OP_EQUAL",
	"!=":"OP_NOTEQUA",
	"+":"OP_PLUS",
	 "-":"OP_MINUS",
	 "*":"OP_MULT",
	 "/":"OP_DIV",
	 "-":"OP_UMINUS",
	 ",":"OP_COMMA",
	 "=":"ASSIGN"
		}


class Scanner:
	def __init__(self):
		self.linecnt = 0
		self.charpos = 0
		self.buffer = []
		self.forwd = 0
		self.follow = 0
		self.linecol = []
		self.idCount = 0
		self.SymbolTable = {}
		self.data = []

	def readInput(self,filename):
		with open(filename) as f: 
		    for line in f:  
		       for ch in line: 
			    
			    if not ch:
			      print "End of file"
			      break
			    else:
			    	self.buffer.append(ch)

		#add sentinel
		self.buffer.append('eof')
		#print(self.buffer)
	#def readInput(self): read input from stdio

	#skip the white space from start of the input
	#however count the line and character count
	def skipWS(self):
		while True:
			if( self.buffer[self.forwd]== " " or self.buffer[self.forwd] =="\n" ):
				self.charpos+=1
				self.forwd+=1
				if(self.buffer[self.forwd] == "\n"):
					self.linecnt+=1
				break

	#return next character
	def peek(self):
		
		if(self.getCurr()=='eof'):
			return "eof"
		return self.buffer[(self.forwd+1)]
	
	#combibne character to obtain a word also check if word is ID or Keyword
	def getword(self):
		while True:
			if(self.isLetter(self.peek()) or  self.isDigit(self.peek()) or self.peek()=="_") :
				self.forwd+=1
			else:
				break
		temp = (self.buffer[self.follow:self.forwd+1])
		word =""
		for ch in temp:
			word+=ch

		#add to smbl table
		if(self.isKeyword(word)):
			self.addtoTable(keyword[word
				],word,self.linecnt,self.follow,self.forwd)
		elif(word == "print"):
			self.addtoTable("PRINT",word,self.linecnt,self.follow,self.forwd)
		elif(word == "return"):
			self.addtoTable("RETURN",word,self.linecnt,self.follow,self.forwd)
		elif(self.isId(word)):
			if(len(word)>= 80):
				temp = word[:80]
				word2=""
				print("Warning::length of Id overflowed, truncating from",word,"to",temp)
				for ch in temp:
					word2+=ch
				self.addtoTable("ID"+str(self.idCount),word2,self.linecnt,self.follow,self.forwd)
				self.idCount+=1
			else:
				self.addtoTable("ID"+str(self.idCount),word,self.linecnt,self.follow,self.forwd)
				self.idCount+=1
	#get number algorithm
	def getNum(self):
		v = 0
		while True:		
			if(self.isDigit(self.peek())):
				v = v*10 + int(self.buffer[self.forwd])
				self.forwd+=1
			else:
				v = v*10 + int(self.buffer[self.forwd])
				if(v> 2147483648 or v < -2147483648 or len(str(v))>10):
					print("WARNING: Size of Integer above limit. ")
				self.addtoTable("ID_INT",v,self.linecnt,self.follow,self.forwd)
				break
	def getOp(self):
		#peek next chracter from buffer if it matches in operator table return else if it does not matches
		#return single operaor else and error
		temp = self.buffer[self.forwd]
		ch = temp[0]
		temp = (self.peek())
		ch+=temp[0]
		if(self.isOp(ch)):
			self.addtoTable(operators[ch],ch,self.linecnt,self.follow,self.forwd)
		#Checking for comment ***[THis section is stored in symbol table]
		elif(ch == "**"):
			if(self.isComment()):
				self.skipComment()
		elif(ch =="<-"):
			if(self.buffer[self.forwd+2] == ">"):
				#print("got exchange")
				self.addtoTable("EXCHANGE",ch+">",self.linecnt,self.follow,self.forwd)
				self.forwd+=2
		else:
			#nknown operators
			#error for u
			print("unknown operator <BUG>",ch)
			#self.forwd+=1
	def skipComment(self):
		temp = ""
		while(self.buffer[self.forwd]!= "\n"):
			if(self.peek()== 'eof'):
				break
			temp+=self.getCurr()
			self.forwd+=1
		self.addtoTable("COMMENT",temp[3:],self.linecnt,self.follow+3,self.forwd)
	def isKeyword(self,ch):
		if(ch in keyword):	
			return True
		else:
			return False
	def isOp(self,ch):
		if(ch in operators):
			return True
		else:
			return (False)
	#check for character if Digit
	def isDigit(self,ch):
		digit = re.compile("[0-9]")
		if(digit.match(ch) == None):
			return False
		else:
			return True
	#check if Character is Letter
	def isLetter(self,ch):

		letter = re.compile("[a-zA-Z]")
		if(letter.match(ch) == None):
			return False
		else:
			return True
	#check If its an ID or not by scanning for alphabet or '_'
	def isId(self,ch):
		count =0 
		for c in  ch:
			ascii = ord(c)
			if(c.isdigit()):
				break
			else:
				if(ascii== 95 or(ascii<=90 and ascii >=65) or(ascii >= 97 and ascii<=122)):
					count +=1
		if(len(ch) == count):
			return True
		else:
			return	False
	def isComment(self):
		if(self.buffer[self.forwd+2] == "*"):
			return True
		else:
			return False
	def isWhite(self):
		if(self.peek() == " " or self.peek() == "\n" or self.peek() == "\t"  ):
			return True
		else:
			return False
	def isotherChar(self,ch):
		if(ch in char):
			self.addtoTable(char[ch],ch,self.linecnt,self.follow,self.forwd)
			return True
		else:
			return False
	def getCurr(self):
		return self.buffer[self.forwd]

	def addtoTable(self,id,val,linecnt,follow,forwd):
		tkObj =tk(id,val,linecnt+1,follow,forwd)
		self.data.append(tkObj)

	def scan(self):
		
		while (self.peek()!='eof'):
			
			if(self.isLetter(self.buffer[self.forwd])):
				self.follow = self.forwd
				if(self.isLetter(self.peek())):
					self.getword()
				elif(self.isWhite()):
					self.getword()
				else:
					self.idCount+=1
					#add to symbol table
					self.addtoTable("ID"+str(self.idCount),self.getCurr(),self.linecnt,self.follow,self.forwd)
					
			elif(self.isDigit(self.buffer[self.forwd])):
				self.follow = self.forwd
				self.getNum()
			elif(self.isOp(self.buffer[self.forwd]) or self.buffer[self.forwd] == "!" ):
				self.follow =self.forwd
				#handle '='error
				if(self.peek() == "\n" or self.peek() == " " or self.isLetter(self.peek()) or self.isDigit(self.peek())):
					#self.addtoTable(operators[self.getCurr()],self.getCurr(),self.linecnt,self.follow,self.forwd)
					print("hello:",self.getCurr())
				else:
					self.getOp()
			elif(self.isotherChar(self.getCurr())):
				self.follow =self.forwd
			elif(self.getCurr() == "\n"):
				
				self.linecnt+=1
				self.linecol.append((self.linecnt,self.forwd))
			else:
				print("illegal charcter used:",self.getCurr())


			self.forwd+=1
#implementing symbol table as Hash Table
#get colmn number from linecol[linenum][0] - startops


print("id\ttype\tlinenum\tstartpos\tendpos\terromsg\t(line,col)")
print("---------------------------------------------------------------------")

token = Scanner()
token.readInput("abc")
token.scan()
for tkobj in token.data:
	tkobj.printall()
