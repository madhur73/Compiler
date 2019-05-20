"""Abstract syntax tree.

ASTs are trees built from the following elements:
- Objects descending from Node
- Tokens (for leaf nodes)
- Python lists
- The value None (for optional elements)

In addition to the AST structure itself, this module also contains the code
for type checking and code generation.
"""

import copy
import itertools
from typing import List, Union, Optional, get_type_hints
from llvmlite import ir

from bmc.errors import ReportableError
from bmc.scope import TupleType, ArrayType, Scope
from bmc.token import Token

class Node:
    """Base class for all abstract syntax tree nodes.
    
    Subclassing Node involves some important magic.  For conciseness, descendents
    of Node are given an auto-generated __init__().  That init accepts keyword-only
    arguments to initialize the node's children.  The names of the children are
    determined by looking at the subclass's type annotations.
    """
    
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
    """Helper for getting the type annotation names belonging to a class, including those from the class's parents.
    
    We can't just use the helper functions from the typing module, because this
    function is called at class creation time - before forward declarations in
    type annotations have a real class to match - causing the functions in the
    typing module to error out.  Anyway, we don't need to resolve the actual
    type of the attribute; we only care about the name.
    """
    annotations = {}
    for c in reversed(cls.mro()):
        annotations.update(getattr(c, "__annotations__", {}))
    return annotations.keys()

def strip_locations(root_element):
    """Return a copy of the given AST element, but with all location information set to None, recursively.
    
    Useful for equality comparisons when you don't care about the locations strictly
    matching, such as in tests.
    
    This is a free function instead of a member function so that it can work on
    lists and None values.
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
    # We copy the whole AST and strip each element in place because
    # we have no easy generic way of constructing a copy of an AST node given
    # the children that we want it to have.
    root_element_copy = copy.deepcopy(root_element)
    recursively_strip_in_place(root_element_copy)
    return root_element_copy


# Root node:

class Program(Node):
    parts: List[Union["Statement", "FunctionDefinition", "Declaration"]]
    def compile(self, error_logger):
        """Compile the whole program as an LLVM module."""
        global_scope = Scope()
        module = ir.Module()
        _add_string_constant(module, "printf_fmt", "%i\n\0")
        ir.Function(module, ir.FunctionType(i32_t, [ir.IntType(8).as_pointer()], var_arg=True), "printf")
        main_function = ir.Function(module, ir.FunctionType(i32_t, []), name="main")
        block = main_function.append_basic_block()
        builder = ir.IRBuilder(block)
        
        for part in self.parts:
            try:
                part.compile(global_scope, builder)
            except SemanticError as e:
                error_logger.log(e)
        
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
    def infer_type(self, scope):
        return TupleType(sum(e.infer_type(scope).length for e in self.elements))
    def compile_slots(self, scope, builder):
        return sum([e.compile_slots(scope, builder) for e in self.elements], [])
    def compile_values(self, scope, builder):
        return sum((e.compile_values(scope, builder) for e in self.elements), [])

# a = b
class AssignmentStatement(Statement):
    left: "LHS"
    right: "Expression"
    def compile(self, scope, builder):
        left_type = self.left.infer_type(scope)
        right_type = self.right.infer_type(scope)
        if left_type != right_type:
            raise SemanticError(f"LHS of assignment ({left_type}) does not match RHS ({right_type}).")
        for slot, value in zip(self.left.compile_slots(scope, builder), self.right.compile_values(scope, builder)):
            # Note that even though we emit stores sequentially, all the slots are
            # compiled at once, and all the values are compiled at once.  This
            # prevents x.0, x.1 = 999, x.0 from incorrectly assigning 999 to x.1
            # through the x.0 assignment that comes before it.
            builder.store(value, slot)

# a <-> b
class ExchangeStatement(Statement):
    left: "LHS"
    right: "LHS"
    def compile(self, scope, builder):
        left_type, right_type = (s.infer_type(scope) for s in (self.left, self.right))
        if left_type != right_type:
            raise SemanticError(f"LHS of exchange ({left_type}) does not match RHS ({right_type}).")
        # See the note in AssignmentStatement.compile() about being careful here
        # to not store anything before everything is loaded.
        left_values, right_values = (s.compile_values(scope, builder) for s in (self.left, self.right))
        left_slots, right_slots = (s.compile_slots(scope, builder) for s in (self.left, self.right))
        for value, slot in itertools.chain(zip(left_values, right_slots), zip(right_values, left_slots)):
            builder.store(value, slot)

# while a == b do ... end while
class WhileStatement(Statement):
    condition: "BooleanExpression"
    body: List["Statement"]
    def compile(self, scope, builder):
        loop_check = builder.append_basic_block("while_loop_check")
        loop_body = builder.append_basic_block("while_loop_body")
        continuation = builder.append_basic_block()
        
        builder.branch(loop_check)
        builder.position_at_end(continuation)
        
        with builder.goto_block(loop_check):
            predicate = self.condition.compile_predicate(scope, builder)
            builder.cbranch(predicate, truebr=loop_body, falsebr=continuation)
        
        with builder.goto_block(loop_body):
            for statement in self.body:
                statement.compile(scope, builder)
            builder.branch(loop_check)

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
    def compile_predicate(self, scope, builder):
        """Returns an LLVM i1 value representing the result of the comparison."""
        if not (self.left.infer_type(scope), self.right.infer_type(scope)) == (TupleType(1), TupleType(1)):
            raise SemanticError("Comparisons can only be made between single integers.")
        [l_value], [r_value] = (e.compile_values(scope, builder) for e in (self.left, self.right))
        return builder.icmp_signed(self.cmpop, l_value, r_value)
class LessThanExpression(BooleanExpression):
    cmpop = "<"
class LessThanEqualsExpression(BooleanExpression):
    cmpop = "<="
class GreaterThanExpression(BooleanExpression):
    cmpop = ">"
class GreaterThanEqualsExpression(BooleanExpression):
    cmpop = ">="
class EqualsExpression(BooleanExpression):
    cmpop = "=="
class NotEqualsExpression(BooleanExpression):
    cmpop = "!="


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
    def compile_values(self, scope, builder):
        if not (self.left.infer_type(scope), self.right.infer_type(scope)) == (TupleType(1), TupleType(1)):
            raise SemanticError("Arithmetic can only be performed on single integers.")
        [l_value], [r_value] = (e.compile_values(scope, builder) for e in (self.left, self.right))
        result = getattr(builder, self.instruction_name)(l_value, r_value)
        return [result]
class AddExpression(ArithmeticExpression):
    instruction_name = "add"
class SubtractExpression(ArithmeticExpression):
    instruction_name = "sub"
class MultiplyExpression(ArithmeticExpression):
    instruction_name = "mul"
class DivideExpression(ArithmeticExpression):
    instruction_name = "sdiv"

# a
class IdentifierExpression(Expression):
    token: Token
    def infer_type(self, scope):
        type, slot = scope.lookup(self.token)
        return type
    def compile_values(self, scope, builder):
        slots = self.compile_slots(scope, builder)
        return [builder.load(slot) for slot in slots]
    def compile_slots(self, scope, builder):
        type, array_slot = scope.lookup(self.token)
        slots = [builder.gep(array_slot, [i32_t(0), i32_t(i)]) for i in range(type.length)]
        return slots

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
        [slot] = self.compile_slots(scope, builder)
        return [builder.load(slot)]
    def compile_slots(self, scope, builder):
        type, slot = scope.lookup(self.identifier_token)
        if not isinstance(type, TupleType):
            raise SemanticError("Only tuples can be indexed.")
        index = int(self.index.string)
        if not 1 <= index <= type.length:
            raise SemanticError("Tuple index out of bounds.  Must be from 1 to " + str(type.length) + ".")
        index -= 1
        return [builder.gep(slot, [i32_t(0), i32_t(index)])]

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


# Code generation stuff.

class SemanticError(ReportableError):
    pass

# LLVM types.  Tuples are represented as LLVM arrays of i32_t.
# Arrays are represented as structs containing a start index, end index, and
# pointer to the beginning of the array.
i32_t = ir.IntType(32)
array_t = ir.LiteralStructType([i32_t, i32_t, i32_t.as_pointer()])

# Helper function for adding a char* global constant to an LLVM module.
def _add_string_constant(module, name, string):
    byte_array = bytearray(string, encoding="utf-8")
    constant_value = ir.ArrayType(ir.IntType(8), len(byte_array))(byte_array)
    global_variable = ir.GlobalVariable(module, constant_value.type, name)
    global_variable.global_constant = True
    global_variable.initializer = constant_value
    return global_variable
