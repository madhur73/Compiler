from bmc.ast import *
from bmc import scanner
from bmc.token import TokenType

class ParseError:
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return self.message

def is_error(x):
	return isinstance(x, ParseError)


def try_consume(scanner, token_type):
	if scanner.peek().type == token_type:
		return scanner.next()
	else:
		return None

def parse_input(scanner):
	parts = []
	while True:
		part = parse_statement(scanner)
		if not part:
			part = parse_declaration(scanner)
		if not part:
			part = parse_definition(scanner)
		if not part:
			break
		parts += [part]
	return Input(parts)

def parse_declaration(scanner):
	# Parse array declarations...
	if try_consume(scanner, TokenType.KW_ARRAY):
		identifier = try_consume(scanner, TokenType.ID)
		if not identifier:
			return ParseError("Expected identifier in array declaration.")
		if not try_consume(scanner, TokenType.LBRAK):
			return ParseError("Expected \"[\" in array declaration.")
		range_ = parse_range(scanner)
		if is_error(range_):
			return range_
		print(scanner.peek())
		if not try_consume(scanner, TokenType.RBRAK):
			return ParseError("Expected \"]\" in array declaration.")
		index_identifier = try_consume(scanner, TokenType.ID)
		index_expression = None
		if index_identifier:
			if not try_consume(scanner, TokenType.ASSIGN):
				return ParseError("Expected \"=\" in array indexing expression.")
			index_expression = parse_expression(scanner)
			if is_error(index_expression):
				return index_expression
		if not try_consume(scanner, TokenType.SEMI):
			return ParseError("Expected \";\" after array declaration.")
		return ArrayDeclaration(identifier, range_, index_identifier, index_expression)
	
	# To do: parse other kinds of declarations.

def parse_range(scanner):
	begin_expression = parse_expression(scanner)
	if is_error(begin_expression):
		return begin_expression
	if not try_consume(scanner, TokenType.OP_DOTDOT):
		return ParseError("Expected \"..\" in range expression.")
	end_expression = parse_expression(scanner)
	if is_error(end_expression):
		return end_expression
	return Range(begin_expression, end_expression)
	
def parse_expression(scanner):
	print("parse_expression", scanner.peek())
	return parse_tuple_expression(scanner)

def parse_tuple_expression(scanner):
	tuple_elements = [parse_addition_expression(scanner)]
	while try_consume(scanner, TokenType.OP_COMMA):
		tuple_elements += [parse_addition_expression(scanner)]
	if len(tuple_elements) == 1:
		return tuple_elements[0]
	else:
		return TupleExpression(tuple_elements)

def parse_addition_expression(scanner):
	left = parse_multiplication_expression(scanner)
	if is_error(left):
		return left
	while scanner.peek().type in (TokenType.OP_PLUS, TokenType.OP_MINUS):
		if scanner.next().type == TokenType.OP_PLUS:
			Node = AddExpression
		else:
			Node = SubtractExpression
		right = parse_multiplication_expression(scanner)
		left = Node(left, right)
	return left

def parse_multiplication_expression(scanner):
	left = parse_parenthesized_expression(scanner)
	if is_error(left):
		return left
	while scanner.peek().type in (TokenType.OP_MULT, TokenType.OP_DIV):
		if scanner.next().type == TokenType.OP_MULT:
			Node = MultiplyExpression
		else:
			Node = DivideExpression
		right = parse_parenthesized_expression(scanner)
		left = Node(left, right)
	return left

def parse_parenthesized_expression(scanner):
	open_parenthesis = try_consume(scanner, TokenType.LPAR)
	if open_parenthesis:
		internal_expression = parse_expression(scanner)
		if not try_consume(scanner, TokenType.RPAR):
			print("Error: Missing ')' to close '('.")
			print(open_parenthesis)
		return internal_expression
	else:
		return parse_id_expression(scanner)

def parse_id_expression(scanner):
	print("parse_id_expression", scanner.peek())
	id_token = try_consume(scanner, TokenType.ID)
	if id_token:
		if try_consume(scanner, TokenType.OP_DOT):
			integer_literal = try_consume(scanner, TokenType.INT_LIT)
			if not integer_literal:
				print("Error: Index of tuple must be an integer literal.")
			return TupleAccessExpression(id_token, integer_literal)
		elif try_consume(scanner, TokenType.LBRAK):
			index_expression = parse_expression(scanner)
			if not try_consume(scanner, TokenType.RBRAK):
				print("Error: Missing ']' to close '['.")
			return ArrayAccessExpression(id_token, index_expression)
		else:
			argument_expression = parse_id_expression(scanner)
			if argument_expression:
				return FunctionCallExpression(id_token, argument_expression)
			else:
				return IdentifierExpression(id_token)
	elif scanner.peek().type == TokenType.INT_LIT:
		return IntegerLiteralExpression(scanner.next())
	else:
		return ParseError("Invalid expression.")

s = scanner.Scanner(string="array a[0..10] i=i*2;")
p = parse_declaration(s)
print(p)		
		
