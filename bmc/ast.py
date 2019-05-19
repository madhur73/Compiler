"""Abstract syntax tree.

ASTs are trees built from the following elements:
- Objects descending from Node
- Tokens (for leaf nodes)
- Python lists
- The value None (for optional elements)
"""

import copy

from bmc.token import Token
from bmc.scope import TupleType, ArrayType, Scope
from typing import List, Union, Optional, get_type_hints
from llvmlite import ir

class SemanticError(Exception):
    pass

i32_t = ir.IntType(32)

# Arrays are represented as a struct containing a start index, end index, and pointer to
# the beginning of the array.
array_t = ir.LiteralStructType([i32_t, i32_t, i32_t.as_pointer()])

def add_string_constant(module, name, string):
    byte_array = bytearray(string, encoding="utf-8")
    constant_value = ir.ArrayType(ir.IntType(8), len(byte_array))(byte_array)
    global_variable = ir.GlobalVariable(module, constant_value.type, name)
    global_variable.global_constant = True
    global_variable.initializer = constant_value
    return global_variable

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
        def __init__(self, **kwargs):
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
    def compile(self):
        # Compile the whole program as an LLVM module.
        global_scope = Scope()
        module = ir.Module()
        add_string_constant(module, "printf_fmt", "%i\n\0")
        ir.Function(module, ir.FunctionType(i32_t, [ir.IntType(8).as_pointer()], var_arg=True), "printf")
        main_function = ir.Function(module, ir.FunctionType(i32_t, []), name="main")
        block = main_function.append_basic_block()
        builder = ir.IRBuilder(block)
        for part in self.parts:
            part.compile(global_scope, builder)
        builder.ret(i32_t(0))
        return module

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
    def compile(self, scope, builder):
        if self.expression:
            rhs_type = self.expression.infer_type(scope)
            if rhs_type == ArrayType:
                raise SemanticError("Initializing from arrays is not allowed.", identifier)
            slot = builder.alloca(ir.ArrayType(i32_t, rhs_type.length))
            values = self.expression.compile_values(scope, builder)
            for i, v in enumerate(values):
                gep = builder.gep(slot, [i32_t(0), i32_t(i)])
                builder.store(v, gep)
            scope.add_global_declaration(self.identifier, rhs_type, slot)
        else:
            # Global variable declared without initialization.
            # We know it will subsequently be initialized as an array, so we can
            # allocate space for an array here.
            slot = builder.alloca(array_t)
            scope.add_global(identifier, slot)

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
    source_sequence: Union["Expression", "Range"]
    body: List["Statement"]

# return x
class ReturnStatement(Statement):
    expression: "Expression"

# print x
class PrintStatement(Statement):
    expression: "Expression"
    def compile(self, scope, builder):
        if self.expression.infer_type(scope) != TupleType(1):
            raise SemanticError("Only single integers can be printed.")
        [value] = self.expression.compile_values(scope, builder)
        printf = builder.module.get_global("printf")
        fmt = builder.module.get_global("printf_fmt")
        gep = builder.gep(fmt, [i32_t(0), i32_t(0)])
        builder.call(printf, [gep, value])

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


# Expressions.
# All expressions implement a compile_values() method that returns a
# list of IR objects representing the result of the expression, suitable for
# assignment.  If the result is a single integer, or an array, it should still
# be wrapped as a single-element list.
class Expression(Node): # Abstract base class.
    pass

# a, b, c
class TupleExpression(Expression):
    elements: List["Expression"]
    def infer_type(self, scope):
        return TupleType(sum(e.infer_type(scope).length for e in self.elements))
    def compile_values(self, scope, builder):
        return sum((e.compile_values(scope, builder) for e in self.elements), [])

# a+b, a-b, a*b, a/b
class ArithmeticExpression(Expression):
    left: "Expression"
    right: "Expression"
    def infer_type(self, scope):
        return TupleType(1)
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
    def infer_type(self, scope):
        return TupleType(1)
    def compile_values(self, scope, builder):
        type, slot = scope.lookup(self.identifier_token)
        if not isinstance(type, TupleType):
            raise SemanticError("Only tuples can be indexed.")
        index = int(self.index.string) - 1
        gep = builder.load(builder.gep(slot, [i32_t(0), i32_t(index)]))
        return [gep]

# a[i]
class ArrayAccessExpression(Expression):
    identifier_token: Token
    index: "Expression"
    def infer_type(self, scope):
        return TupleType(1)

# 123
class IntegerLiteralExpression(Expression):
    token: Token
    def infer_type(self, scope):
        return TupleType(1)
    def compile_values(self, scope, builder):
        return [i32_t(int(self.token.string))]
