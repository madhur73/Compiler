"""Abstract syntax tree.

ASTs are trees built from the following elements:
- Objects descending from Node
- Tokens (for leaf nodes)
- Python lists
- The value None (for optional elements)
"""

import copy

from bmc.token import Token
from typing import List, Union, Optional, get_type_hints

class Node:
    """Base class for all abstract syntax tree nodes."""
    
    def __repr__(self):
        def indent(string):
            return "\n".join("  " + line for line in string.split("\n"))
        def pretty(value):
            # For non-empty lists, start a new level of indentation and put each element on its own line.
            if isinstance(value, list) and len(value) > 0:
                return "[\n" + indent(",\n".join(repr(e) for e in value)) + "\n]"
            else:
                return repr(value)
        child_strings = [indent(name + " = " + pretty(value)) for name, value in self.children()]
        return type(self).__name__ + "(\n" + ",\n".join(child_strings) + "\n)"
    
    def children(self):
        return [i for i in vars(self).items()]
    
    # Auto-generates the node class's __init__().
    def __init_subclass__(subclass):
        child_names = _type_annotation_names(subclass)
        def __init__(self, *, location_begin=None, location_end=None, **kwargs):
            self.location_begin = location_begin
            self.location_end = location_end
            for name in child_names:
                setattr(self, name, kwargs.pop(name))
            if kwargs:
                raise TypeError("Unrecognized arguments in Node initialization: " + str(kwargs))
        subclass.__init__ = __init__
    
    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return self.children() == other.children()


def _type_annotation_names(cls):
    annotations = dict()
    for c in reversed(cls.mro()):
        annotations.update(getattr(c, "__annotations__", {}))
    return annotations.keys()

def strip_locations(root_element):
    """Return a copy of the given AST element, but with all location information set to None, recursively.
    
    Useful for equality comparisons when you don't care about the locations strictly
    matching, such as in tests.
    """
    def recursively_strip_in_place(element):
        if isinstance(element, list):
            for list_element in element:
                recursively_strip_in_place(list_element)
        elif isinstance(element, Token):
            element.begin = None
            element.end = None
            element.line = None
            element.column = None
        elif isinstance(element, Node):
            element.location_begin = None
            element.location_end = None
            for child_name, child in element.children():
                recursively_strip_in_place(child)
    root_element_copy = copy.deepcopy(root_element)
    recursively_strip_in_place(root_element_copy)
    return root_element_copy

        
# Descendents of Node are given an auto-generated __init__().  The node's children
# are passed in as keyword-only arguments; the names of these arguments are
# specified by type annotations.  Additionally, the __init__() accepts optional
# location_begin and location_end arguments, representing the [begin, end) source
# file offsets of the node.


# Root node:

class Program(Node):
    parts: List[Union["Statement", "FunctionDefinition", "Declaration"]]


# Declarations:

class Declaration(Node): # Abstract base class.
    pass

# array a[0..9] = i=i*2
class ArrayDeclaration(Declaration):
    identifier: Token
    range: "Range"
    index_identifier: Optional[Token]
    index_expression: Optional["Expression"]

# local x = 1
class LocalDeclaration(Declaration):
    identifier: Token
    expression: Optional["Expression"]

# global x = 1
class GlobalDeclaration(Declaration):
    identifier: Token
    expression: Optional["Expression"]

# Definitions:

# defun f(a, b, c) ... end defun
class FunctionDefinition(Node):
    function_identifier: Token
    argument_identifiers: List[Token]
    body: List[Union["Declaration", "Statement"]]


# Statements:

class Statement(Node): # Abstract base class.
    pass

# a, t.1, a[1]
class LHS(Node):
    elements: List[Union["IdentifierExpression", "TupleAccessExpression", "ArrayAccessExpression"]]

# a = b
class AssignmentStatement(Statement):
    left: "LHS"
    right: "Expression"

# a <-> b
class ExchangeStatement(Statement):
    left: "LHS"
    right: "LHS"

# while a == b do ... end while
class WhileStatement(Statement):
    condition: "BooleanExpression"
    body: List["Statement"]

# if a == b then ... end if
class IfStatement(Statement):
    condition: "BooleanExpression"
    body: List["Statement"]
    else_body: List["Statement"]

# foreach i in s do ... end for
class ForeachStatement(Statement):
    element_identifier: Token
    source_sequence: Union["IdentifierExpression", "Range"]
    body: List["Statement"]

# return x
class ReturnStatement(Statement):
    expression: "Expression"

# print x
class PrintStatement(Statement):
    expression: "Expression"


# Expressions:

# a..b
class Range(Node):
    begin_expression: "Expression"
    end_expression: "Expression"

# a < b, a == b, etc.
class BooleanExpression(Node):
    left: "Expression"
    right: "Expression"
class LessThanExpression(BooleanExpression): pass
class LessThanEqualsExpression(BooleanExpression): pass
class GreaterThanExpression(BooleanExpression): pass
class GreaterThanEqualsExpression(BooleanExpression): pass
class EqualsExpression(BooleanExpression): pass
class NotEqualsExpression(BooleanExpression): pass

class Expression(Node): # Abstract base class.
    pass

# a, b, c
class TupleExpression(Expression):
    elements: List["Expression"]

# a+b, a-b, a*b, a/b
class ArithmeticExpression(Expression):
    left: "Expression"
    right: "Expression"
class AddExpression(ArithmeticExpression): pass
class SubtractExpression(ArithmeticExpression): pass
class MultiplyExpression(ArithmeticExpression): pass
class DivideExpression(ArithmeticExpression): pass

# a
class IdentifierExpression(Expression):
    token: Token

# f x
class FunctionCallExpression(Expression):
    identifier_token: Token
    argument: "Expression"

# t.1
class TupleAccessExpression(Expression):
    identifier_token: Token
    index: Token

# a[i]
class ArrayAccessExpression(Expression):
    identifier_token: Token
    index: "Expression"

# 123
class IntegerLiteralExpression(Expression):
    token: Token
