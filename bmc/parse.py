from bmc.ast import *
from bmc import scanner
from bmc.token import TokenType

class ParseError:
	"""When encountering an error, parse functions return this instead of an AST node."""
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return "Parse error: " + self.message
	def tack_on(self, message):
		return ParseError(self.message + " " + message)

def is_error(x):
	return isinstance(x, ParseError)

def try_consume(scanner, token_type):
	"""Returns the next token if its type matches token_type, else None."""
	if scanner.peek().type == token_type:
		return scanner.next()
	else:
		return None

def parse_input(scanner):
	parts = []
	while True:
		part = parse_statement(scanner)
		if is_error(part):
			part = parse_declaration(scanner)
		if is_error(part):
			part = parse_definition(scanner)
		if is_error(part):
			break
		parts += [part]
	if scanner.peek().type == TokenType.EOF:
		return Input(parts)
	else:
		return part

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
			return range_.tack_on("in array declaration")
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
				return index_expression.tack_on("in array declaration")
		if not try_consume(scanner, TokenType.SEMI):
			return ParseError("Expected \";\" after array declaration.")
		return ArrayDeclaration(identifier, range_, index_identifier, index_expression)
	
	# Parse non-array (global or local) declarations...
	else:
		if try_consume(scanner, TokenType.KW_LOCAL):
			NodeType = LocalDeclaration
		elif try_consume(scanner, TokenType.KW_GLOBAL):
			NodeType = GlobalDeclaration
		else:
			return ParseError("Expected \"array\", \"global\", or \"local\" in declaration.")
		identifier = try_consume(scanner, TokenType.ID)
		if not identifier:
			return ParseError("Expected identifier in declaration.")
		if not try_consume(scanner, TokenType.ASSIGN):
			return ParseError("Expected \"=\" in declaration.")
		expression = parse_expression(scanner)
		if is_error(expression):
			return expression.tack_on("in declaration")
		if not try_consume(scanner, TokenType.SEMI):
			return ParseError("Expected \";\" after declaration.")
		return NodeType(identifier, expression)

def parse_definition(scanner):
	if not try_consume(scanner, TokenType.KW_DEFUN):
		return ParseError("Expected \"defun\" in function definiton.")
	function_identifier = try_consume(scanner, TokenType.ID)
	if not function_identifier:
		return ParseError("Expected function identifier.")
	if not try_consume(scanner, TokenType.LPAR):
		return ParseError("Expected \"(\" after function identifier.")
	first_argument_identifier = try_consume(scanner, TokenType.ID)
	if not first_argument_identifier:
		return ParseError("Function definitions must have at least one argument.")
	argument_identifiers = [first_argument_identifier]
	while try_consume(scanner, TokenType.OP_COMMA):
		next_argument_identifier = try_consume(scanner, TokenType.ID)
		if not next_argument_identifier:
			return ParseError("Expected another argument identifier after comma in argument list.")
		argument_identifiers += [next_argument_identifier]
	if not try_consume(scanner, TokenType.RPAR):
		return ParseError("Expected \")\" after argument list.")
	
	# Parse body.
	body = []
	while True:
		statement_or_declaration = parse_statement(scanner)
		if is_error(statement_or_declaration):
			statement_or_declaration = parse_declaration(scanner)
		if is_error(statement_or_declaration):
			break
		body += [statement_or_declaration]
		
	if not try_consume(scanner, TokenType.KW_END):
		return ParseError("Expected \"end\" after function definition.")
	if not try_consume(scanner, TokenType.KW_DEFUN):
		return ParseError("Expected \"end\" after function definition.")
	return FunctionDefinition(function_identifier, argument_identifiers, body)

def parse_statement(scanner):
	lhs_list = parse_lhs_list(scanner)
	if not is_error(lhs_list):
		if try_consume(scanner, TokenType.ASSIGN):
			rhs = parse_expression(scanner)
			if is_error(rhs):
				return rhs.tack_on("in assignment statement")
			node = AssignmentStatement(lhs_list, rhs)
		elif try_consume(scanner, TokenType.EXCHANGE):
			rhs_list = parse_lhs_list(scanner)
			if is_error(rhs_list):
				return rhs_list.tack_on("in exchange statement")
			node = ExchangeStatement(lhs_list, rhs_list)
		if not try_consume(scanner, TokenType.SEMI):
			return ParseError("Expected \";\" after assignment or exchange statement.")
		return node
	elif try_consume(scanner, TokenType.KW_WHILE):
		conditional = parse_boolean_expression(scanner)
		if is_error(conditional):
			return conditional.tack_on("in while statement")
		if not try_consume(TokenType.KW_DO):
			return ParseError("Expected \"do\" after while conditional.")
		statements = parse_statement_list(scanner)
		if not (try_consume(TokenType.KW_END) and try_consume(TokenType.KW_WHILE)):
			return ParseError("Expected \"end while\" after while loop.")
		return WhileStatement(condition, statements)
	elif try_consume(scanner, TokenType.KW_IF):
		condition = parse_boolean_expression(scanner)
		if is_error(condition):
			return condition.tack_on("in if statement")
		if not try_consume(scanner, TokenType.KW_THEN):
			return ParseError("Expected \"then\".")
		statements = parse_statement_list(scanner)
		root_node = IfStatement(condition, statements, [])
		rightmost_node = root_node
		while try_consume(scanner, TokenType.KW_ELSIF):
			elsif_condition = parse_boolean_expression(scanner)
			if is_error(elsif_condition):
				return condition.tack_on("in elsif statement")
			if not try_consume(scanner, TokenType.KW_THEN):
				return ParseError("Expected \"then\" after elsif conditional.")
			elsif_statements = parse_statement_list(scanner)
			if is_error(elsif_statements):
				return elsif_statements.tack_on("in elsif statement")
			new_node = IfStatement(elsif_condition, elsif_statements, [])
			rightmost_node.else_statements = [new_node]
			rightmost_node = new_node
		if try_consume(scanner, TokenType.KW_ELSE):
			else_statements = parse_statement_list(scanner)
			if is_error(else_statements):
				return else_statements.tack_on("in else statement")
			rightmost_node.else_statements = else_statements
			if not (try_consume(scanner, TokenType.KW_END) and try_consume(scanner, TokenType.KW_IF)):
				return ParseError("Expected \"end if\" after if-elsif-else.")
		return root_node
	elif try_consume(scanner, TokenType.KW_FOREACH):
		identifier = try_consume(scanner, TokenType.ID)
		if not identifier:
			return ParseError("Expected identifier in foreach")
			
		
	else:
		return ParseError("Invalid statement.")

def parse_statement_list(scanner):
	statements = []
	while True:
		statement = parse_statement(scanner)
		if is_error(statement):
			return statements
		statements += [statement]

def parse_lhs_list(scanner):
	item = parse_lhs_item(scanner)
	if is_error(item):
		return item.tack_on("in lhs list")
	items = [item]
	while try_consume(scanner, TokenType.OP_COMMA):
		next_item = parse_lhs_item(scanner)
		if is_error(next_item):
			return next_item.tack_on("in lhs list")
		items += [next_item]
	return items

def parse_lhs_item(scanner):
	id_token = try_consume(scanner, TokenType.ID)
	if not id_token:
		return ParseError("Expected identifier in lhs-item.")
	if try_consume(scanner, TokenType.OP_DOT):
		integer_literal = try_consume(scanner, TokenType.INT_LIT)
		if not integer_literal:
			return ParseError("Error: Index of tuple must be an integer literal.")
		return TupleAccessExpression(id_token, integer_literal)
	elif try_consume(scanner, TokenType.LBRAK):
		index_expression = parse_expression(scanner)
		if not try_consume(scanner, TokenType.RBRAK):
			return ParseError("Error: Missing ']' to close '['.")
		return ArrayAccessExpression(id_token, index_expression)
	else:
		return IdentifierExpression(id_token)
	
def parse_range(scanner):
	begin_expression = parse_expression(scanner)
	if is_error(begin_expression):
		return begin_expression.tack_on("in range expression")
	if not try_consume(scanner, TokenType.OP_DOTDOT):
		return ParseError("Expected \"..\" in range expression.")
	end_expression = parse_expression(scanner)
	if is_error(end_expression):
		return end_expression.tack_on("in range expression")
	return Range(begin_expression, end_expression)

def parse_boolean_expression(scanner):
	left = parse_expression(scanner)
	if is_error(left):
		return left.tack_on("in boolean expression")
	operator = scanner.peek().type
	NodeType = {
		TokenType.OP_LESS:         LessThanExpression,
		TokenType.OP_GREATER:      GreaterThanExpression,
		TokenType.OP_EQUAL:        EqualsExpression,
		TokenType.OP_NOTEQUA:      NotEqualsExpression,
		TokenType.OP_LESSEQUAL:    LessThanEqualsExpression,
		TokenType.OP_GREATEREQUAL: GreaterThanEqualsExpression,
	}.get(operator)
	if NodeType is None:
		return ParseError("Expected boolean operator in boolean expression.")
	scanner.next()
	right = parse_expression(scanner)
	if is_error(right):
		return right.tack_on("in boolean expression")
	return NodeType(left, right)

def parse_expression(scanner):
	expression = parse_tuple_expression(scanner)
	if is_error(expression):
		expression = expression.tack_on("in expression")
	return expression

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
			return ParseError("Error: Missing ')' to close '('.")
		return internal_expression
	else:
		return parse_id_expression(scanner)
		
def parse_id_expression(scanner):
	id_token = try_consume(scanner, TokenType.ID)
	if id_token:
		if try_consume(scanner, TokenType.OP_DOT):
			integer_literal = try_consume(scanner, TokenType.INT_LIT)
			if not integer_literal:
				return ParseError("Error: Index of tuple must be an integer literal.")
			return TupleAccessExpression(id_token, integer_literal)
		elif try_consume(scanner, TokenType.LBRAK):
			index_expression = parse_expression(scanner)
			if not try_consume(scanner, TokenType.RBRAK):
				return ParseError("Error: Missing ']' to close '['.")
			return ArrayAccessExpression(id_token, index_expression)
		else:
			argument_expression = parse_id_expression(scanner)
			if not is_error(argument_expression):
				return FunctionCallExpression(id_token, argument_expression)
			else:
				return IdentifierExpression(id_token)
	elif scanner.peek().type == TokenType.INT_LIT:
		return IntegerLiteralExpression(scanner.next())
	else:
		return ParseError("Invalid expression.")

source = """
global a = 1, 2, 3;

defun main(argA, argB, argC)
	local b = 456;
	if 1 == 1 then
		x=1;
		if 2 == 2 then
			x=2;
			if 3 == 3 then
				x = 3;
			end if
		end if
	end if
end defun
"""
s = scanner.Scanner(emit_comments=False, string=source)
p = parse_input(s)
print(p)
print(s.peek())
		
