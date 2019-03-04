class token:
	def __init__(self,id,typenm,linenum,startpos,endpos):
		self.id = id
		self.type = typenm
		self.linenum = linenum
		self.startpos =startpos
		self.endpos = endpos
		self.errormsg = ""
		self.colstart = 0

	def setlincol(self,linecol):
		temp = (linecol[self.linenum]-self.endpos)
		if(temp<0):
			self.colend = (self.linenum,temp*(-1))
		else:
			self.colend = (self.linenum,temp*(-1))
		print(self.colend)
    
	def printall(self):	
		print(self.id+"\t"+str(self.type)+"\t"+str(self.linenum)+"\t"+str(self.startpos)+"\t"+str(self.endpos)+"\t"+self.errormsg+"\t")

	def seterror(self,msg):
		self.errormsg = msg
    
	def geterrormsg(self):
		print(self.errormsg+"on line:",self.linenum,"on col start:",self.colstart, "col end:")


