"""Classes for keeping track of all the variables in the current scope, as well as their types."""

from collections import namedtuple

class TupleType:
    """Represents the type of a tuple variable.  Integers are modeled as 1-tuples."""
    def __init__(self, length):
        assert length > 0
        self.length = length
    def __repr__(self):
        return f"TupleType({self.length})"
    def __eq__(self, other):
        return isinstance(other, TupleType) and self.length == other.length

# TODO: Figure out a nice way to expose the most recent values for each element
# of a tuple.

class ArrayType:
    """Represents the type of an array variable.  Does not have to be instantiated; ArrayType is equivalent to ArrayType()."""
    def __new__(cls):
        return cls
    @staticmethod
    def __repr__():
        return "ArrayType()"

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.namespace = {}
    def is_global():
        return self.parent == None
    def add_global_declaration(self, token, type, slot):
        self.namespace[token.string] = token, type, slot
    def lookup(self, token):
        token, type, slot = self.namespace[token.string]
        return type, slot
