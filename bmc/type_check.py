"""Contains some helper code for type checking.

Note that some of the type checking code, such as the code for inferring the
type of an expression, is in ast.py as methods on the AST node classes.
"""

from bmc import ast
from bmc.token import Token, TokenType
import collections

class Scope(collections.abc.MutableMapping):
	"""Represents, at some point in the program, the list of visible symbols.
	
	variables and functions are keyed by either an identifier string or an ID
	token containing an identifier string.  Each value is a Symbol object.
	"""
	def __init__(self):
		self.namespace = {}
	@staticmethod
	def _adjust_key(key):
		if isinstance(key, Token) and key.type == TokenType.ID:
			return key.string
		elif isinstance(key, str):
			return key
		else:
			raise TypeError()
	def __getitem__(self, key):
		try:
			return self.namespace[self._adjust_key(key)]
		except KeyError as error:
			raise TypeCheckError("Reference to undefined function or variable.", key)
	def __setitem__(self, key, value):
		self.namespace[self._adjust_key(key)] = value
	def __delitem__(self, key):
		del self.namespace[self._adjust_key(key)]
	def __iter__(self):
		return iter(self.namespace)
	def __len__(self):
		return len(self.namespace)

class Symbol:
	def __init__(self, declaration_node, initialization_node, type=None):
		self.declaration_node = declaration_node
		self.initialization_node = initialization_node
		self.type = type

class ArrayType():
	"""Used to mark that a symbol is an array."""
	pass
def is_array_type(object):
	return isinstance(object, ArrayType)

class TupleType:
	"""Used to mark that a symbol is a tuple, of the given length."""
	def __init__(self, length):
		self.length = length
	def __eq__(self, other):
		return self.length == other.length if type(other) is TupleType else NotImplemented
def is_tuple_type(object):
	return isinstance(object, TupleType)

class FunctionType:
	"""Used to mark that a symbol is a function taking an argumen_type argument (which may be TupleType(1) or ArrayType) and returning a return_type."""
	def __init__(self, argument_type, return_type):
		self.argument_type = argument_type
		self.return_type = return_type
def is_function_type(object):
	return isinstance(object, FunctionType)

class TypeCheckError(Exception):
	"""Thrown when the type checker encounters a problem.
	
	problem_node is the AST node or token where the problem occurs.
	"""
	def __init__(self, message, problem_node):
		Exception.__init__(self, message)
		self.problem_node = problem_node

def check_top_level_declaration(declaration_node, scope):
	if declaration_node.identifier.string in scope:
		raise TypeCheckError("Redeclaration of global variable.", declaration_node)
	elif isinstance(declaration_node, ast.LocalDeclaration):
		raise TypeCheckError("Local declarations cannot appear at the top level.", declaration_node)
	elif isinstance(declaration_node, ast.ArrayDeclaration):
		scope[declaration_node.identifier.string] = Symbol(declaration_node, None, ArrayType())
		print("Declared global array", declaration_node.identifier)
	elif isinstance(declaration_node, ast.GlobalDeclaration):
		type = None
		initialization_node = None
		if declaration_node.expression is not None:
			type = infer_type(declaration_node.expression, scope)
			initialization_node = declaration_node
		scope[declaration_node.identifier.string] = Symbol(declaration_node, initialization_node, type)

def type_check(program_node):
	global_scope = {}
	for global_statement in program_node.parts:
		if isinstance(global_statement, ast.Declaration):
			check_top_level_declaration(global_statement)
