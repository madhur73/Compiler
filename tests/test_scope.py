import pytest
from bmc import scope, token

def new_token(identifier):
    return token.Token(token.TokenType.ID, identifier, 0, 0, 0, 0)

def test_global_or_local():
    a = scope.Scope()
    b = scope.Scope(a)
    c = scope.Scope(b)
    assert a.is_global()
    assert not b.is_global()
    assert not c.is_global()

def test_global_tuple_lookup():
    s = scope.Scope()
    s.add_global_declaration(new_token("x"), scope.TupleType(1), "x_slot")
    s.add_global_declaration(new_token("y"), scope.TupleType(2), "y_slot")
    assert s.lookup(new_token("x")) == (scope.TupleType(1), "x_slot")
    assert s.lookup(new_token("y")) == (scope.TupleType(2), "y_slot")

@pytest.mark.xfail
def test_shadowing():
    outer = scope.Scope()
    outer.add_global_declaration(new_token("x"), scope.TupleType(1), None)
    inner = scope.Scope(outer)
    inner.add_global_declaration(new_token("x"), scope.TupleType(2), None)
    assert outer.lookup(new_token("x")) == (scope.TupleType(1), None)
    assert inner.lookup(new_token("x")) == (scope.TupleType(2), None)
