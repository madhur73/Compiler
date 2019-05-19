"""Classes for keeping track of all the variables in the current scope, as well as their types."""

from collections import namedtuple
from bmc.errors import ReportableError

class ScopeError(ReportableError):
    pass

class TupleType:
    """Represents the type of a tuple variable.  Integers are modeled as 1-tuples."""
    def __init__(self, length):
        assert length > 0
        self.length = length
    def __repr__(self):
        return f"TupleType({self.length})"
    def __eq__(self, other):
        return isinstance(other, TupleType) and self.length == other.length

class ArrayType:
    """Represents the type of an array variable.  Does not have to be instantiated; ArrayType is equivalent to ArrayType()."""
    def __new__(cls):
        return cls
    @staticmethod
    def __repr__():
        return "ArrayType()"

class Scope:
    """Represents the set of variables available for use at a certain point in the program.
    
    For convenience, variables are looked up by passing in tokens whose values
    represent their identifier.
    
    Scopes can be nested.  Name lookups in the inner scopes will fall back to the outer scopes.
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.namespace = {}
    def is_global(self):
        """Returns whether this is the global scope."""
        return self.parent == None
    def add_global_declaration(self, token, type, slot):
        """Add a global declaration.
        
        This corresponds both to creating new global variables in the global
        scope, and to declaring global references in function scopes.
        
        If type is None, slot should also be None.  If this is the global scope,
        An array declaration is expected to follow.
        
        If type is a TupleType, slot should be an LLVM pointer value that points
        to the LLVM array containing the tuple elements.  The scope must be
        global, in this case.
        """
        
        if not self.is_global():
            raise ScopeError("Non-global scopes are not yet implemented.", token) 
        elif token.string in self.namespace:
            raise ScopeError(f"Global variable {token.string} already declared.", token)
        else:
            self.namespace[token.string] = token, type, slot
    
    def add_array_declaration(self, token, slot):
        """Add an array declaration.
        
        The token must have been previously associated with a global or local
        declaration in this scope with an empty type and slot.
        """
        # Ensure the variable is present in the current scope, even though
        # we're about to overwrite its type and slot.
        _, _ = self.current_scope_lookup(token)
        self.namespace[token.string] = token, ArrayType, slot
    
    def lookup(self, token):
        try:
            return self.current_scope_lookup(token)
        except ScopeError:
            if self.parent:
                return self.parent.lookup(token)
            else:
                raise ScopeError(f"Variable {token.string} is undeclared.", token)
    
    def current_scope_lookup(self, token):
        """Finds a variable in the current scope."""
        try:
            token, type, slot = self.namespace[token.string]
            return type, slot
        except KeyError:
            return ScopeError(f"Variable {token.string} is undeclared.", token)
    
    def global_lookup(self, token):
        pass
