
from bmc.ast import *
from bmc import scanner
from bmc.token import TokenType as T
from copy import copy

def parse_report_errors(scanner):
	try:
		ast = parse_program(scanner)
		print("Success!")
		print(ast)
		return ast
	except ParseError as error:
		print("Error.")
		print("Got", scanner.peek())
		print("But expected " + " or ".join(str(t) for t in error.expected))
	
class ParseError(Exception):
	"""Exception for parse errors.
	
	This is thrown by the parser upon encountering a syntax error.  Higher
	levels of the parser may catch it to attempt error recovery.  This is also
	used to implement alternatives in the grammar: when the first choice fails,
	it throws this exception, signifying that the second choice should be tried.
	
	expected is a set of TokenTypes that would have avoided this error.
	"""
	def __init__(self, expected):
		self.expected = expected

def parse_any(scanner, parsers):
	"""Implements parsing alternatives, e.g. "A = B|C".
	
	parsers is an iterable of recursive descent parsing functions taking a single
	Scanner argument.  Each is attempted in order.  The result of the first one
	not to throw a ParseError is returned.  If they all throw ParseErrors, a new
	ParseError is thrown.
	
	This assumes that the alternatives are all left-factored.  A parser may only
	fail in a context where the next alternative can pick up from the same
	position, without rolling back the scanner.
	"""
	expected = set()
	original_next_token = scanner.peek()
	for parser in parsers:
		try:
			return parser(scanner)
		except ParseError as parse_error:
			if scanner.peek() == original_next_token:
				# OK: merely a failure to parse that alternative.
				expected |= parse_error.expected
			else:
				# Error: alternative failed mid-way through, after we had
				# committed to it.
				raise parse_error
	raise ParseError(expected=expected)

def parse_repeating(scanner, repeating_parser, next_token):
	"""Implements parsing repetitions, e.g. "A = B*c".
	
	repeating_parser(scanner) is like B in the example above.  It is repeatedly
	called until it fails.
	
	next_token(scanner) is like c in the example above.  If it is not None, a
	match is attempted after the first failure of repeating_parser.  If that
	fails, then the result of the parse_repeating() call is a failure.
	
	The return value is a list of the repeating_parser results.  The next_token
	result is discarded (unless it is an error).
	"""
	repeating_parser_results = []
	try:
		while True:
			start_token = scanner.peek()
			repeating_parser_results += [repeating_parser(scanner)]
	except ParseError as error:
		if scanner.peek() != start_token:
			# Error was a legitimate error in the middle of repeating_parser,
			# not merely a signal that the repetitions have ended.
			raise error
		else:
			expected = error.expected.copy()
	try:
		if next_token is not None:
			parse_token(scanner, next_token)
		return repeating_parser_results
	except ParseError as error: # next_parser failed.
		expected |= error.expected
		raise ParseError(expected=expected)

def parse_token(scanner, token_type):
	"""Parses a token, given a token type that it must match.
	
	The actual Token object, which includes the token string, is returned.
	If the token does not match, a ParseError is raised before it is consumed.
	"""
	if scanner.peek().type == token_type:
		return scanner.next()
	else:
		raise ParseError(expected=set([token_type]))

def parse_token_sequence(scanner, token_types):
	"""Like parse_token, but parses multiple tokens in sequence, and returns a list of Token objects."""
	return [parse_token(scanner, t) for t in token_types]

def parse_program(scanner):
	def parse_statement_or_declaration_or_definition(scanner):
		return parse_any(scanner, [parse_statement, parse_declaration, parse_definition])
	def parse_eof(scanner):
		return parse_token(scanner, T.EOF)
	
	parts = []
	while scanner.peek().type != T.EOF:
		parts += [parse_statement_or_declaration_or_definition(scanner)]
	return Program(parts)

def parse_array_declaration(scanner):
	_, identifier, _ = parse_token_sequence(scanner, [T.KW_ARRAY, T.ID, T.LBRAK])
	range = parse_range(scanner)
	parse_token(scanner, T.RBRAK)
	
	# Parse optional initialization expression.
	try:
		index_identifier = parse_token(scanner, T.ID)
	except ParseError:
		index_identifier = None
	if index_identifier is not None:
		parse_token(scanner, T.ASSIGN)
		index_expression = parse_expression(scanner)
		pass
	else:
		index_expression = None
	
	parse_token(scanner, T.SEMI)
	
	return ArrayDeclaration(identifier, range, index_identifier, index_expression)

def parse_non_array_declaration(scanner):
	def parse_local(scanner):
		return parse_token(scanner, T.KW_LOCAL)
	def parse_global(scanner):
		return parse_token(scanner, T.KW_GLOBAL)
	NodeType = {
		T.KW_LOCAL: LocalDeclaration,
		T.KW_GLOBAL: GlobalDeclaration
	}[parse_any(scanner, [parse_local, parse_global]).type]
	
	identifier, _ = parse_token_sequence(scanner, [T.ID, T.ASSIGN])
	expression = parse_expression(scanner)
	parse_token(scanner, T.SEMI)
	return NodeType(identifier, expression)

def parse_declaration(scanner):
	return parse_any(scanner, [
	    parse_array_declaration,
	    parse_non_array_declaration
	])

def parse_definition(scanner):
	_, function_identifier, _ = parse_token_sequence(scanner, [T.KW_DEFUN, T.ID, T.LPAR])
	
	# Parse argument list.  At least one argument is required.
	argument_identifiers = [parse_token(scanner, T.ID)]
	def parse_next_id(scanner):
		parse_token(scanner, T.OP_COMMA)
		return parse_token(scanner, T.ID)
	argument_identifiers += parse_repeating(scanner, parse_next_id, T.RPAR)
	
	# Parse body.
	def parse_statement_or_declaration(scanner):
		return parse_any(scanner, [parse_statement, parse_declaration])
	body = parse_repeating(scanner, parse_statement_or_declaration, T.KW_END)
	
	parse_token(scanner, T.KW_DEFUN)
	
	return FunctionDefinition(function_identifier, argument_identifiers, body)

def parse_assign_or_exchange_statement(scanner):
	lhs_list = parse_lhs_list(scanner)
	NodeType = {
		T.ASSIGN: AssignmentStatement,
		T.EXCHANGE: ExchangeStatement
	}[parse_any(scanner, [
	    lambda s: parse_token(s, T.ASSIGN),
	    lambda s: parse_token(s, T.EXCHANGE)
	]).type]
	if NodeType is AssignmentStatement:
		rhs = parse_expression(scanner)
	else:
		rhs = parse_lhs_list(scanner)
	parse_token(scanner, T.SEMI)
	return NodeType(lhs_list, rhs)

def parse_while_statement(scanner):
	parse_token(scanner, T.KW_WHILE)
	conditional = parse_boolean_expression(scanner)
	parse_token(scanner, T.KW_DO)
	statements = parse_statement_list(scanner, T.KW_END)
	parse_token_sequence(scanner, [T.KW_WHILE])
	return WhileStatement(conditional, statements)

def parse_if_statement(scanner):
	parse_token(scanner, T.KW_IF)
	condition = parse_boolean_expression(scanner)
	parse_token(scanner, T.KW_THEN)
	statements = parse_statement_list(scanner, None)
	
	root_node = IfStatement(condition, statements, [])
	rightmost_node = root_node
	while scanner.peek().type == T.KW_ELSIF:
		scanner.next()
		elsif_condition = parse_boolean_expression(scanner)
		parse_token(scanner, T.KW_THEN)
		elsif_statements = parse_statement_list(scanner, None)
		new_node = IfStatement(elsif_condition, elsif_statements, [])
		rightmost_node.else_statements = [new_node]
		rightmost_node = new_node
	if scanner.peek().type == T.KW_ELSE:
		scanner.next()
		rightmost_node.else_statements = parse_statement_list(scanner, None)
	
	parse_token_sequence(scanner, [T.KW_END, T.KW_IF])
	return root_node

def parse_foreach_statement(scanner):
	_, identifier, _ = parse_token_sequence(scanner, [T.KW_FOREACH, T.ID, T.KW_IN])
	source_range_or_identifier = parse_any(scanner, [
		parse_range,
		lambda s: IdentifierExpression(parse_token(s, T.ID))
	])
	parse_token(scanner, T.KW_DO)
	statements = parse_statement_list(scanner, T.KW_END)
	parse_token_sequence(scanner, [T.KW_FOR])
	return ForeachStatement(identifier, source_range_or_identifier, statements)

def parse_return_statement(scanner):
	parse_token(scanner, T.RETURN)
	expression = parse_expression(scanner)
	parse_token(scanner, T.SEMI)
	return ReturnStatement(expression)
	
def parse_print_statement(scanner):
	parse_token(scanner, T.PRINT)
	expression = parse_expression(scanner)
	parse_token(scanner, T.SEMI)
	return PrintStatement(expression)

def parse_statement(scanner):
	return parse_any(scanner, [
	    parse_assign_or_exchange_statement,
	    parse_while_statement,
	    parse_if_statement,
	    parse_foreach_statement,
	    parse_return_statement,
	    parse_print_statement
	])
	
def parse_statement_list(scanner, next_token):
	return parse_repeating(scanner, parse_statement, next_token)

def parse_lhs_list(scanner):
	def parse_next_lhs_item(scanner):
		parse_token(scanner, T.OP_COMMA)
		return parse_lhs_item(scanner)
	items = [parse_lhs_item(scanner)]
	items += parse_repeating(scanner, parse_next_lhs_item, None)
	return items

def parse_lhs_item(scanner):
	id_token = parse_token(scanner, T.ID)
	if scanner.peek().type == T.OP_DOT:
		scanner.next()
		integer_literal = parse_token(scanner, T.INT_LIT)
		return TupleAccessExpression(id_token, integer_literal)
	elif scanner.peek().type == T.LBRAK:
		scanner.next()
		index_expression = parse_expression(scanner)
		parse_token(scanner, T.RBRAK)
		return ArrayAccessExpression(id_token, index_expression)
	else:
		return IdentifierExpression(id_token)
	
def parse_range(scanner):
	begin_expression = parse_expression(scanner)
	parse_token(scanner, T.OP_DOTDOT)
	end_expression = parse_expression(scanner)
	return Range(begin_expression, end_expression)

def parse_boolean_expression(scanner):
	left = parse_expression(scanner)
	NodeType = {
		T.OP_LESS:         LessThanExpression,
		T.OP_GREATER:      GreaterThanExpression,
		T.OP_EQUAL:        EqualsExpression,
		T.OP_NOTEQUA:      NotEqualsExpression,
		T.OP_LESSEQUAL:    LessThanEqualsExpression,
		T.OP_GREATEREQUAL: GreaterThanEqualsExpression,
	}[parse_any(scanner, [
	    lambda s: parse_token(scanner, T.OP_LESS),
	    lambda s: parse_token(scanner, T.OP_GREATER),
	    lambda s: parse_token(scanner, T.OP_EQUAL),
	    lambda s: parse_token(scanner, T.OP_NOTEQUA),
	    lambda s: parse_token(scanner, T.OP_LESSEQUAL),
	    lambda s: parse_token(scanner, T.OP_GREATEREQUAL)
	]).type]
	right = parse_expression(scanner)
	return NodeType(left, right)

def parse_expression(scanner):
	return parse_tuple_expression(scanner)

def parse_tuple_expression(scanner):
	tuple_elements = [parse_addition_expression(scanner)]
	def parse_next_tuple_element(scanner):
		parse_token(scanner, T.OP_COMMA)
		return parse_addition_expression(scanner)
	tuple_elements += parse_repeating(scanner, parse_next_tuple_element, None)
	if len(tuple_elements) == 1:
		return tuple_elements[0]
	else:
		return TupleExpression(tuple_elements)

def parse_addition_expression(scanner):
	left = parse_multiplication_expression(scanner)
	while scanner.peek().type in (T.OP_PLUS, T.OP_MINUS):
		if scanner.next().type == T.OP_PLUS:
			Node = AddExpression
		else:
			Node = SubtractExpression
		right = parse_multiplication_expression(scanner)
		left = Node(left, right)
	return left

def parse_multiplication_expression(scanner):
	left = parse_parenthesized_expression(scanner)
	while scanner.peek().type in (T.OP_MULT, T.OP_DIV):
		if scanner.next().type == T.OP_MULT:
			Node = MultiplyExpression
		else:
			Node = DivideExpression
		right = parse_parenthesized_expression(scanner)
		left = Node(left, right)
	return left

def parse_parenthesized_expression(scanner):
	try:
		parse_token(scanner, T.LPAR)
		parenthesized = True
	except ParseError:
		parenthesized = False
	if parenthesized:
		internal_expression = parse_expression(scanner)
		parse_token(scanner, T.RPAR)
	else:
		internal_expression = parse_id_expression(scanner)
	return internal_expression
		
def parse_id_expression(scanner):
	if scanner.peek().type == T.ID:
		id_token = scanner.next()
		if scanner.peek().type == T.OP_DOT:
			scanner.next()
			integer_literal = parse_token(scanner, T.INT_LIT)
			return TupleAccessExpression(id_token, integer_literal)
		elif scanner.peek().type == T.LBRAK:
			scanner.next()
			index_expression = parse_expression(scanner)
			parse_token(scanner, T.RBRAK)
			return ArrayAccessExpression(id_token, index_expression)
		else:
			try:
				argument_expression = parse_parenthesized_expression(scanner)
				return FunctionCallExpression(id_token, argument_expression)
			except ParseError:
				return IdentifierExpression(id_token)
	elif scanner.peek().type == T.INT_LIT:
		return IntegerLiteralExpression(scanner.next())
	else:
		raise ParseError(expected=set([T.ID, T.INT_LIT]))
