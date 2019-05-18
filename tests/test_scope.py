from bmc import scope

def test_tuple_type():
    assert scope.TupleType(1) != scope.TupleType(2)
    assert scope.TupleType(1) == scope.TupleType(1)

def test_array_type():
    assert scope.ArrayType is scope.ArrayType()
    assert scope.ArrayType() is scope.ArrayType()

def test_different_types():
    assert scope.ArrayType != scope.TupleType(1)
