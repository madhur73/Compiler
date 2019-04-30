from bmc.token import Token
from bmc.type_check import *
from typing import List, Union
from functools import reduce

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
	
	def all_tokens(self):
		def tokens_of(child):
			if isinstance(child, Token):
				return [child]
			elif isinstance(child, Node):
				return child.all_tokens()
			elif isinstance(child, list):
				return sum([tokens_of(e) for e in child], [])
		# Flat list of child tokens.
		child_tokens = sum([tokens_of(child) for _, child in self.children()], [])
		return child_tokens
	
	def source(self):
		def merge(range1, range2):
			return min(range1[0], range2[0]), max(range1[1], range2[1])
		all_tokens = self.all_tokens()
		ranges = [(token.begin, token.end) for token in all_tokens]
		overall_range = reduce(merge, ranges)
		source = all_tokens[0].full_source[overall_range[0]:overall_range[1]]
		return source

class Program(Node):
	parts: List[Union["Statement", "FunctionDefinition", "Declaration"]]
	def __init__(self, parts):
		self.parts = parts
	def type_check(self):
		scope = Scope()
		for part in self.parts:
			try:
				part.type_check(scope)
			except TypeCheckError as error:
				print(error)
		for symbol in scope:
			if scope[symbol].type is None:
				print(TypeCheckError("Symbol was never defined.", symbol.declaration_node))

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
	def type_check(self, scope):
		if self.identifier not in scope:
			raise TypeCheckError("Array must be declared with \"global\" or \"local\" before it is initialized as an array.", self)
		elif scope[self.identifier].initialization_node is not None:
			raise TypeCheckError("Array has already been initialized.", self)
		else:
			scope[self.identifier].initialization_node = self
			scope[self.identifier].type = ArrayType()

class NonArrayDeclaration(Declaration):
	identifier: Token
	expression: "Expression"
	def __init__(self, identifier, expression):
		self.identifier = identifier
		self.expression = expression
class LocalDeclaration(NonArrayDeclaration):
	def type_check(self, scope):
		if scope.is_top_level():
			raise TypeCheckError("Only global variables can be declared in the global scope.", self)
class GlobalDeclaration(NonArrayDeclaration):
	def type_check(self, scope):
		if self.identifier in scope:
			raise TypeCheckError("Redeclaration of variable.", self)
		elif not scope.is_top_level() and expression is not None:
			raise TypeCheckError("Global variables cannot be initialized from a function.", self)
		else:
			new_global_type = None if self.expression is None else self.expression.infer_type(scope)
			scope[self.identifier] = Symbol(self, self.expression, new_global_type)

class FunctionDefinition(Node):
	function_identifier: Token
	argument_identifiers: List[Token]
	def __init__(self, function_identifier, argument_identifiers, body):
		self.function_identifier = function_identifier
		self.argument_identifiers = argument_identifiers
		self.body = body
	def type_check(self, scope):
		pass

class Statement(Node):
	pass

class AssignmentStatement(Statement):
	left: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right
	def type_check(self, scope):
		left_types = [e.infer_type(scope) for e in self.left]
		for type, expression in zip(left_types, self.left):
			if not is_tuple_type(type):
				raise TypeCheckError("Element in left hand side of assignment statement must be assignable.", expression)
		right_type = self.right.infer_type(scope)
		effective_left_length = sum(e.length for e in left_types)
		if effective_left_length != right_type.length:
			raise TypeCheckError(f"Length mismatch between left ({effective_left_length}) and right ({right_type.length}) of assignment statement.", self)

class ExchangeStatement(Statement):
	left: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	right: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]
	def __init__(self, left, right):
		self.left = left
		self.right = right
	def type_check(self, scope):
		pass

class WhileStatement(Statement):
	condition: "BooleanExpression"
	statements: List["Statement"]
	def __init__(self, condition, statements):
		self.condition = condition
		self.statements = statements
	def type_check(self, scope):
		pass

class IfStatement(Statement):
	condition: "BooleanExpression"
	statements: List["Statement"]
	else_statements: List["Statement"]
	def __init__(self, condition, statements, else_statements):
		self.condition = condition
		self.statements = statements
		self.else_statements = else_statements
	def type_check(self, scope):
		pass

class ForeachStatement(Statement):
	element_identifier: Token
	sequence: Union["IdentifierExpression", "Range"]
	statements: List["Statement"]
	def __init__(self, element_identifier, sequence, statements):
		self.element_identifier = element_identifier
		self.sequence = sequence
		self.statements = statements
	def type_check(self, scope):
		pass

class ReturnStatement(Statement):
	expression: "Expression"
	def __init__(self, expression):
		self.expression = expression
	def type_check(self, scope):
		pass

class PrintStatement(Statement):
	expression: "Expression"
	def __init__(self, expression):
		self.expression = expression
	def type_check(self, scope):
		pass

# array-id omitted as a node type because it's syntactically identical to an ID.

class Range(Node):
	begin_expression: "Expression"
	end_expression: "Expression"
	def __init__(self, begin_expression, end_expression):
		self.begin_expression = begin_expression
		self.end_expression = end_expression
	def type_check(self, scope):
		pass

class BooleanExpression(Node):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right
	def type_check(self, scope):
		pass
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
	def infer_type(self, scope):
		subexpression_types = [s.infer_type(scope) for s in self.elements]
		for type, subexpression in zip(subexpression_types, self.elements):
			if not is_tuple_type(type):
				raise TypeCheckError("Tuple can only be constructed from other tuples or scalars.", subexpression)
		flattened_length = sum(type.length for type in subexpression_types)
		return TupleType(flattened_length)

class ArithmeticExpression(Expression):
	left: "Expression"
	right: "Expression"
	def __init__(self, left, right):
		self.left = left
		self.right = right
	def infer_type(self, scope):
		left_type = infer_type(self.left, scope)
		if not is_tuple_type(left_type) and left_type.length == 1:
			raise TypeCheckError("Expected scalar but got a tuple.", self.left)
		right_type = infer_type(self.right, scope)
		if not is_tuple_type(right_type) and right_type.length == 1:
			raise TypeCheckError("Expected scalar but got a tuple.", self.right)
		return TupleType(1)
class AddExpression(ArithmeticExpression):
	pass
class SubtractExpression(ArithmeticExpression):
	pass
class MultiplyExpression(ArithmeticExpression):
	pass
class DivideExpression(ArithmeticExpression):
	pass

class IdentifierExpression(Expression):
	identifier_token: Token
	def __init__(self, identifier_token):
		self.identifier_token = identifier_token
	def infer_type(self, scope):
		return scope[self.identifier_token].type

class FunctionCallExpression(Expression):
	identifier_token: Token
	argument: "Expression"
	def __init__(self, identifier_token, argument):
		self.identifier_token = identifier_token
		self.argument = argument
	def infer_type(self, scope):
		return TupleType(1)
		# To do: Properly infer the return type here.
		
class TupleAccessExpression(Expression):
	tuple_expression: "Expression"
	index: Token
	def __init__(self, tuple_expression, index):
		self.tuple_expression = tuple_expression
		self.index = index
	def infer_type(self, scope):
		type = infer_type(tuple_expression)
		if is_tuple_type(type):
			if int(index.string) <= type.length:
				return TupleType(1)
			raise TypeCheckError(f"Invalid tuple index {index.string} for {type.length}-tuple.", self)
		raise TypeCheckError("Expression is not a tuple.", self.tuple_expression)

class ArrayAccessExpression(Expression):
	identifier: Token
	index: "Expression"
	def __init__(self, identifier, index):
		self.identifier = identifier
		self.index = index
	def infer_type(self, scope):
		if identifier in scope and is_array_type(scope[identifier].type):
			# Valid array use.
			return TupleType(1)
		else:
			raise TypeCheckError("Identifier does not name an array.", self)

class IntegerLiteralExpression(Expression):
	token: Token
	def __init__(self, token):
		self.token = token
	def infer_type(self, scope):
		# For simplicity, integers are treated as 1-tuples.
		return TupleType(1)
