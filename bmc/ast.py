from bmc import token

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
		def indented(string):
			lines = string.split("\n")
			indented_lines = ("  " + line for line in lines)
			return "\n".join(indented_lines)
		def pretty(value):
			if isinstance(value, list):
				return "[\n" + indented("\n".join(str(e) for e in value)) + "\n]"
			else:
				return str(value)
		result = type(self).__name__
		child_strings = [name + " = " + pretty(value) for name, value in self.children()]
		if child_strings:
			result += "\n"
			result += "\n".join(indented(child_string) for child_string in child_strings)
		return result
	
	def children(self):
		return (i for i in vars(self).items())

class Program(Node):
	def __init__(self, parts):
		self.parts = parts

class Declaration(Node):
	pass

class ArrayDeclaration(Declaration):
	def __init__(self, identifier, range, index_identifier, index_expression):
		self.identifier = identifier
		self.range = range
		self.index_identifier = index_identifier
		self.index_expression = index_expression

class NonArrayDeclaration(Declaration):
	def __init__(self, identifier, expression):
		self.identifier = identifier
		self.expression = expression
class LocalDeclaration(NonArrayDeclaration): pass
class GlobalDeclaration(NonArrayDeclaration): pass

class FunctionDefinition(Node):
	def __init__(self, function_identifier, argument_identifiers, body):
		self.function_identifier = function_identifier
		self.argument_identifiers = argument_identifiers
		self.body = body

class Statement(Node):
	pass

class AssignmentStatement(Statement):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class ExchangeStatement(Statement):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class WhileStatement(Statement):
	def __init__(self, condition, statements):
		self.condition = condition
		self.statements = statements

class IfStatement(Statement):
	def __init__(self, condition, statements, else_statements):
		self.condition = condition
		self.statements = statements
		self.else_statements = else_statements

class ForeachStatement(Statement):
	def __init__(self, element_identifier, sequence, statements):
		self.element_identifier = element_identifier
		self.sequence = sequence
		self.statements = statements

class ReturnStatement(Statement):
	def __init__(self, expression):
		self.expression = expression

class PrintStatement(Statement):
	def __init__(self, expression):
		self.expression = expression

# array-id omitted as a node type because it's syntactically identical to an ID.

class Range(Node):
	def __init__(self, begin_expression, end_expression):
		self.begin_expression = begin_expression
		self.end_expression = end_expression

class BooleanExpression(Node):
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
	def __init__(self, elements):
		self.elements = elements

class AddExpression(Expression):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class SubtractExpression(Expression):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class MultiplyExpression(Expression):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class DivideExpression(Expression):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class IdentifierExpression(Expression):
	def __init__(self, identifier_token):
		self.identifier_token = identifier_token

class FunctionCallExpression(Expression):
	def __init__(self, identifier_token, argument):
		self.identifier_token = identifier_token
		self.argument = argument

class TupleAccessExpression(Expression):
	def __init__(self, tuple_expression, index):
		self.tuple_expression = tuple_expression
		self.index = index

class ArrayAccessExpression(Expression):
	def __init__(self, id, index):
		self.id = id
		self.index = index

class IntegerLiteralExpression(Expression):
	def __init__(self, token):
		self.token = token
