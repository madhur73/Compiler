import pytest
from bmc import token, scanner, parse, ast

def check_ast(source, expected_ast):
    __tracebackhide__ = True
    if not isinstance(expected_ast, ast.Program):
        if not isinstance(expected_ast, list):
            expected_ast = [expected_ast]
        expected_ast = ast.Program(parts=expected_ast)
    s = scanner.Scanner(string=source)
    actual_ast = ast.strip_locations(parse.parse_program(s))
    assert actual_ast == expected_ast

def id_token(string):
    return token.Token(token.TokenType.ID, string, None, None, None, None)

def int_token(string):
    return token.Token(token.TokenType.INT_LIT, string, None, None, None, None)

def test_assignment_statement():
    expected = ast.AssignmentStatement(
        left=ast.LHS(elements=[
            ast.IdentifierExpression(token=id_token("a")),
            ast.TupleAccessExpression(identifier_token=id_token("b"), index=int_token("1")),
            ast.ArrayAccessExpression(identifier_token=id_token("c"), index=ast.IntegerLiteralExpression(token=int_token("2")))
        ]),
        right = ast.TupleExpression(elements=[
            ast.IntegerLiteralExpression(token=int_token("0")),
            ast.IntegerLiteralExpression(token=int_token("1")),
            ast.IntegerLiteralExpression(token=int_token("2"))
        ])
    )
    check_ast("a, b.1, c[2] = 0, 1, 2;", expected)

def test_foreach_statement():
    expected = ast.ForeachStatement(
        element_identifier = id_token("i"),
        source_sequence = ast.Range(
            begin_expression = ast.IntegerLiteralExpression(token=int_token("1")),
            end_expression = ast.IntegerLiteralExpression(token=int_token("10"))
        ),
        body = [
            ast.PrintStatement(
                expression = ast.IdentifierExpression(token=id_token("i"))
            )
        ]
    )
    check_ast("foreach i in 1..10 do print i; end for", expected)
    
    expected = ast.ForeachStatement(
        element_identifier = id_token("e"),
        source_sequence = ast.IdentifierExpression(token=id_token("a")),
        body = [
            ast.PrintStatement(
                expression = ast.IdentifierExpression(token=id_token("e"))
            )
        ]
    )
    
    check_ast("foreach e in a do print e; end for", expected)

