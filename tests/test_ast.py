import pytest
from bmc import ast

def test_init_requires_named_arguments():
    with pytest.raises(TypeError):
        n = ast.EqualsExpression("a", "b")
    n = ast.EqualsExpression(left="a", right="b")
    assert (n.left, n.right) == ("a", "b")

def test_init_rejects_extra_arguments():
    with pytest.raises(TypeError):
        n = ast.EqualsExpression(left="a", right="b", extra="c")

def test_init_accepts_optional_location():
    n = ast.EqualsExpression(left="a", right="b", location_begin=0, location_end=1)
    assert (n.location_begin, n.location_end) == (0, 1)

def test_equality():
    x_lt_y_1 = ast.LessThanExpression(left="x", right="y")
    x_lt_y_2 = ast.LessThanExpression(left="x", right="y")
    x_gt_y = ast.GreaterThanExpression(left="x", right="y")
    y_gt_x = ast.GreaterThanExpression(left="y", right="x")
    assert x_lt_y_1 == x_lt_y_2 # Equal: same type, same contents.
    assert x_lt_y_1 != x_gt_y # Not equal: same structure but different type.
    assert x_gt_y != y_gt_x # Not equal: same type but different contents.
    
def test_repr():
    n = ast.IfStatement(
        condition=ast.LessThanExpression(
            left=ast.IdentifierExpression(token="i"),
            right=ast.IntegerLiteralExpression(token="123")
        ),
        body=[ast.PrintStatement(expression=ast.IdentifierExpression(token="x"))],
        else_body=[]
    )
    namespace = {}
    exec("from bmc.ast import *; m = " + repr(n), globals(), namespace)
    assert n == namespace["m"]
