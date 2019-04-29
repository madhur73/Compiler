from bmc.token import Token
from typing import List, Union

class Node:
	"""Base class for all abstract syntax tree nodes.
	
	Defines common code for testing equality and for pretty-printing through str().
	"""
	def __eq__(self, other):
		"""Returns whether or not the two trees have the same structure.
		
		For nodes holding tokens, only the type and string value of the tokens
		need to be equal; the source location is ignored.
		"""
		pass
	
	def __str__(self):
		def indent(string):
			return "\n".join("  " + line for line in string.split("\n"))
		def pretty(value):
			# For non-empty lists, start a new level of indentation and put each element on its own line.
			if isinstance(value, list) and len(value) > 0:
				return "[\n" + indent(",\n".join(str(e) for e in value)) + "\n]"
			else:
				return str(value)
		child_strings = [indent(name + " = " + pretty(value)) for name, value in self.children()]
		return type(self).__name__ + "(\n" + ",\n".join(child_strings) + "\n)"
	
	def children(self):
		return (i for i in vars(self).items())

class Program(Node):
	parts: List[Union["Statement", "FunctionDefinition", "Declaration"]]
	def __init__(self, parts):
		self.parts = parts

class Declaration(Node):
	pass

class ArrayDeclaration(Declaration):
	identifier: Token
	range: "Range"
	index_identifier: Token
	index_expression: "Expression"
	def __init__(self, identifier, range, index_identifier, index_expression):
		self.identifier = identifier
		self.range = range
		self.index_identifier = index_identifier
		self.index_expression = index_expression

class NonArrayDeclaration(Declaration):
	identifier: Token
	expression: "Expression"
	def __init__(self, identifier, expression):
		self.identifier = identifier
		self.expression = expression
class LocalDeclaration(NonArrayDeclaration): pass
class GlobalDeclaration(NonArrayDeclaration): pass

class FunctionDefinition(Node):
	function_identifier: Token
	argument_identifiers: List[Token]
	def __init__(self, function_identifier, argument_identifiers, body):
		self.function_identifier = function_identifier
		self.argument_identifiers = argument_identifiers
		self.body = body

class Statement(Node):
	pass

class AssignmentStatement(Statement):
	left: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right

class ExchangeStatement(Statement):
	left: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	right: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	def __init__(self, left, right):
		self.left = left
		self.right = right

class WhileStatement(Statement):
	condition: "BooleanExpression"
	statements: List["Statement"]
	def __init__(self, condition, statements):
		self.condition = condition
		self.statements = statements

class IfStatement(Statement):
	condition: "BooleanExpression"
	statements: List["Statement"]
	else_statements: List["Statement"]
	def __init__(self, condition, statements, else_statements):
		self.condition = condition
		self.statements = statements
		self.else_statements = else_statements

class ForeachStatement(Statement):
	element_identifier: Token
	sequence: Union["IdentifierExpression", "Range"]
	statements: List["Statement"]
	def __init__(self, element_identifier, sequence, statements):
		self.element_identifier = element_identifier
		self.sequence = sequence
		self.statements = statements

class ReturnStatement(Statement):
	expression: "Expression"
	def __init__(self, expression):
		self.expression = expression

class PrintStatement(Statement):
	expression: "Expression"
	def __init__(self, expression):
		self.expression = expression

# array-id omitted as a node type because it's syntactically identical to an ID.

class Range(Node):
	begin_expression: "Expression"
	end_expression: "Expression"
	def __init__(self, begin_expression, end_expression):
		self.begin_expression = begin_expression
		self.end_expression = end_expression

class BooleanExpression(Node):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right
class LessThanExpression(BooleanExpression): pass
class LessThanEqualsExpression(BooleanExpression): pass
class GreaterThanExpression(BooleanExpression): pass
class GreaterThanEqualsExpression(BooleanExpression): pass
class EqualsExpression(BooleanExpression): pass
class NotEqualsExpression(BooleanExpression): pass

class Expression(Node):
	"""Base class for all kinds of expressions."""
	pass

class TupleExpression(Expression):
	elements: List["Expression"]
	def __init__(self, elements):
		self.elements = elements

class AddExpression(Expression):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right

class SubtractExpression(Expression):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right

class MultiplyExpression(Expression):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right

class DivideExpression(Expression):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right

class IdentifierExpression(Expression):
	identifier_token: Token
	def __init__(self, identifier_token):
		self.identifier_token = identifier_token

class FunctionCallExpression(Expression):
	identifier_token: Token
	argument: "Expression"
	def __init__(self, identifier_token, argument):
		self.identifier_token = identifier_token
		self.argument = argument

class TupleAccessExpression(Expression):
	tuple_expression: "Expression"
	index: Token
	def __init__(self, tuple_expression, index):
		self.tuple_expression = tuple_expression
		self.index = index

class ArrayAccessExpression(Expression):
	identifier: Token
	index: "Expression"
	def __init__(self, identifier, index):
		self.identifier = identifier
		self.index = index

class IntegerLiteralExpression(Expression):
	token: Token
	def __init__(self, token):
		self.token = token
