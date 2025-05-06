from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from functools import reduce
from typing import Dict, List, Optional, Tuple, Union

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Attribute, MLContext, Operation
from xdsl.passes import ModulePass

from choco.ast_visitor import Visitor
from choco.dialects import choco_ast, choco_type
from choco.semantic_error import SemanticError


class Type(ABC):
    @staticmethod
    def from_op(op: Operation) -> "Type":
        if isinstance(op, choco_ast.TypeName):
            name = op.type_name.data  # type: ignore
            if name == "int":
                return int_type
            if name == "bool":
                return bool_type
            if name == "str":
                return str_type
            if name == "<None>":
                return none_type
            if name == "<Empty>":
                return empty_type
            if name == "object":
                return object_type
            raise Exception(f"Found type with unknown name `{name}'")
        if isinstance(op, choco_ast.ListType):
            elem_type = Type.from_op(op.elem_type.op)
            return ListType(elem_type)
        raise Exception(f"Found {op}, expected TypeName or ListType")

    @staticmethod
    def from_attribute(attr: Attribute) -> "Type":
        if isinstance(attr, choco_type.NamedType):
            name: str = attr.type_name.data  # type: ignore
            if name == "int":
                return int_type
            if name == "bool":
                return bool_type
            if name == "str":
                return str_type
            if name == "<None>":
                return none_type
            if name == "<Empty>":
                return empty_type
            if name == "object":
                return object_type
            raise Exception(f"Found type with unknown name `{name}'")
        if isinstance(attr, choco_type.ListType):
            elem_type = Type.from_attribute(attr.elem_type)  # type: ignore
            return ListType(elem_type)
        raise Exception(f"Found {attr}, expected TypeName or ListType")


@dataclass
class BasicType(Type):
    name: str


@dataclass
class ListType(Type):
    elem_type: Type


class BottomType(Type):  # "⊥"
    pass


class ObjectType(Type):  # "object"
    pass


@dataclass
class FunctionType(Type):  # input0 x ... x inputN -> output
    inputs: List[Type]
    output: Type


int_type = BasicType("int")
bool_type = BasicType("bool")
str_type = BasicType("str")
none_type = BasicType("<None>")
empty_type = BasicType("<Empty>")
bottom_type = BottomType()
object_type = ObjectType()

arith_op = ["+", "-", "*", "//", "%"]
cmp_op = ["==", "<", ">", "<=", ">=", "!="]
log_op = ["or", "and"]

def to_attribute(t: Type) -> Attribute:
    if t == int_type:
        return choco_type.int_type
    elif t == bool_type:
        return choco_type.bool_type
    elif t == str_type:
        return choco_type.str_type
    elif t == none_type:
        return choco_type.none_type
    elif t == empty_type:
        return choco_type.empty_type
    elif t == object_type:
        return choco_type.object_type
    elif isinstance(t, ListType):
        elem_type = to_attribute(t.elem_type)
        return choco_type.ListType([elem_type])
    else:
        raise Exception(f"Can't translate {t} into an attribute")


def join(t1: Type, t2: Type) -> Type:
    if is_assignment_compatible(t1, t2):
        return t2
    if is_assignment_compatible(t2, t1):
        return t1
    else:
        return object_type


def is_subtype(t1: Type, t2: Type) -> bool:
    if t1 == t2:
        return True
    elif t2 == object_type and (
        t1 == int_type or t1 == bool_type or t1 == str_type or isinstance(t1, ListType)
    ):
        return True
    elif t1 == none_type and t2 == object_type:
        return True
    elif t1 == empty_type and t2 == object_type:
        return True
    elif t1 == bottom_type:
        return True
    else:
        return False


def is_assignment_compatible(t1: Type, t2: Type) -> bool:

    if is_subtype(t1, t2) and t1 != bottom_type:
        return True
    elif (
        (t1 == none_type)
        and t2 != int_type
        and t2 != bool_type
        and t2 != str_type
        and t2 != bottom_type
    ):
        return True
    elif (isinstance(t2, ListType) and t1 == empty_type):
        return True
    elif (
        isinstance(t2, ListType)
        and isinstance(t1, ListType)
        and t1.elem_type == none_type
        and is_assignment_compatible(none_type, t2.elem_type)
    ):
        return True
    else:
        return False


def check_assignment_compatibility(t1: Type, t2: Type):
    if not is_assignment_compatible(t1, t2):
        raise SemanticError(f" Expected {t1} and {t2} to be assignment compatible")


def check_type(found: Type, expected: Type):
    if found != expected:
        raise SemanticError(f"Found `{found}' but expected {expected}")


def check_subtype(found: Type, expected: Type):
    if not is_subtype(found, expected):
        raise SemanticError(f"Found `{found}' but expected a subtype of {expected}")


def check_list_type(found: Type) -> Type:
    if not isinstance(found, ListType):
        raise SemanticError(f"Found `{found}' but expected a list type")
    else:
        return found.elem_type


@dataclass
class FunctionInfo:
    func_type: FunctionType
    params: List[str]
    nested_defs: List[Tuple[str, Type]]

    def __post_init__(self):
        if len(self.func_type.inputs) != len(self.params):
            raise Exception(f"Expected same number of input types and parameter names")


LocalEnvironment = Dict[str, Union[Type, FunctionInfo]]


class TypeChecking(ModulePass):
    name = "type-checking"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        o = build_env(op)
        r = bottom_type

        program = op.ops.first
        assert isinstance(program, choco_ast.Program)
        defs = list(program.defs.ops)
        if len(defs) >= 1:
            check_stmt_or_def_list(o, r, defs)
        stmts = list(program.stmts.ops)
        if len(stmts) >= 1:
            check_stmt_or_def_list(o, r, stmts)


# Build local environments
def build_env(module: ModuleOp) -> LocalEnvironment:
    o: LocalEnvironment = {
        "len": FunctionInfo(FunctionType([object_type], int_type), ["arg"], []),
        "print": FunctionInfo(FunctionType([object_type], none_type), ["arg"], []),
        "input": FunctionInfo(FunctionType([], str_type), [], []),
    }

    @dataclass
    class BuildEnvVisitor(Visitor):
        o: LocalEnvironment

        def visit_typed_var(self, typed_var: choco_ast.TypedVar):
            name, type = typed_var.var_name.data, Type.from_op(  # type: ignore
                typed_var.type.op
            )
            self.o.update({name: type})

        def traverse_func_def(self, func_def: choco_ast.FuncDef):
            f: str = func_def.func_name.data  # type: ignore
            # collect function parameter names and types
            xs: List[str] = []
            ts: List[Type] = []
            for op in func_def.params.ops:
                assert isinstance(op, choco_ast.TypedVar)
                name, type = op.var_name.data, Type.from_op(op.type.op)  # type: ignore
                xs.append(name)
                ts.append(type)
            # collect return type
            t = (
                Type.from_op(func_def.return_type.op)
                if (len(func_def.return_type.ops) == 1)
                else none_type
            )
            # collect nested variable definitions
            body_visitor = BuildEnvVisitor({})
            for op in func_def.func_body.ops:
                body_visitor.traverse(op)
            vs: List[Tuple[str, Type]] = []
            for var_name, var_type in body_visitor.o.items():
                assert isinstance(var_type, Type)
                vs.append((var_name, var_type))

            o.update({f: FunctionInfo(FunctionType(ts, t), xs, vs)})

    BuildEnvVisitor(o).traverse(module)

    return o


# Dispatch to typing rules to decide which rule to invoke

def check_stmt_or_def_list(o: LocalEnvironment, r: Type, ops: List[Operation]):
    return stmt_def_list_rule(o, r, ops)

def check_stmt_or_def(o: LocalEnvironment, r: Type, op: Operation):
    if isinstance(op, choco_ast.VarDef):
        typed_var = op.typed_var.op
        assert isinstance(typed_var, choco_ast.TypedVar)
        id = typed_var.var_name.data
        t = Type.from_op(typed_var.type.op)
        e1 = op.literal.op
        return var_init_rule(o, r, id, t, e1)
    elif isinstance(op, choco_ast.Assign):
        return assign_rule(o, r, op)
    elif isinstance(op, choco_ast.Pass):
        return pass_rule(o, r, op)
    elif isinstance(op, choco_ast.Return):
        return return_rule(o, r, op)
    elif isinstance(op, choco_ast.If):
        return if_else_rule(o, r, op)
    elif isinstance(op, choco_ast.While):
        return while_rule(o, r, op)
    elif isinstance(op, choco_ast.For):
        return for_rule(o, r, op)
    elif isinstance(op, choco_ast.GlobalDecl):
        if o.get(op.decl_name.data) is  None:
            raise SemanticError(f"Global variable {op.id.data} not in outer context")
        return
    elif isinstance(op, choco_ast.NonLocalDecl):
        if o.get(op.decl_name.data) is  None:
            raise SemanticError(f"Non-Local variable {op.id.data} not in outer context")
        return
    elif isinstance(op, choco_ast.FuncDef):
        return func_def_rule(o, r, op)
    else:
        return expr_stmt_rule(o, r, op)

def check_expr(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    t: Optional[Type] = None
    if isinstance(op, choco_ast.Literal):
        t = literal_rules(o, r, op)
    elif isinstance(op, choco_ast.UnaryExpr):
        op_name = op.op.data  # type: ignore
        e = op.value.op
        if op_name == "-":
            t = negate_rule(o, r, e)
        elif op_name == "not":
            t = not_rule(o, r, op)
        else:
            raise SemanticError("Attempted unary operation with invalid operation")
    elif isinstance(op, choco_ast.BinaryExpr):
        t = None
        t_l = check_expr(o, r, op.lhs.block._first_op)
        # arithmetic
        if op.op.data in arith_op:
            if t_l == int_type:
                t = arith_rule(o, r, op)
            elif t_l == str_type:
                t = str_concat_rule(o, r, op)
            elif isinstance(t_l, ListType):
                t = list_concat_rule(o, r, op)
        # comparisons
        if op.op.data in cmp_op:
            if t_l == int_type:
                t = int_compare_rule(o, r, op)
            elif t_l == str_type:
                t = str_compare_rule(o, r, op)
            elif t_l == bool_type:
                t = bool_compare_rule(o, r, op)
        # is
        if op.op.data == "is":
            t = is_rule(o, r, op)
        # and
        if op.op.data == "and":
            t = and_rule(o, r, op)
        # or
        if op.op.data == "or":
            t = or_rule(o, r, op)
        if not t:
            raise SemanticError("Attempted binary operation with invalid operation")
    elif isinstance(op, choco_ast.ExprName):
        t = var_read_rule(o, r, op.id.data)  # type: ignore
    elif isinstance(op, choco_ast.IfExpr):
        e0 = op.cond.op
        e1 = op.then.op
        e2 = op.or_else.op
        t = cond_rule(o, r, e1, e0, e2)
    elif isinstance(op, choco_ast.IndexExpr):
        t = check_expr(o, r, op.value.op)
        if t == str_type:
            t = str_select_rule(o, r, op)
        else:
            t = list_select_rule(o, r, op)
    elif isinstance(op, choco_ast.ListExpr):
        t = list_display_rule(o, r, op)
    elif isinstance(op, choco_ast.CallExpr):
        t = invoke_rule(o, r, op)

    assert isinstance(t, Type)

    op.properties["type_hint"] = to_attribute(t)

    return t

# Typing rules, each typing rule is implemented by a corresponding function

# [VAR-READ] rule
# O, R |- id: T
def var_read_rule(o: LocalEnvironment, r: Type, id: str) -> Type:
    # O(id) = T, where T is not a function type.
    t = o.get(id)
    if t is None:
        raise SemanticError(f"Unknown identifier {id} used")
    if isinstance(t, FunctionInfo):
        raise SemanticError(
            f"Function identifier `{id}' used where value identifier expected"
        )
    return t

# [VAR-INIT] rule
# O, R |- id: T = e1
def var_init_rule(o: LocalEnvironment, r: Type, id: str, t: Type,  e1: Operation):
    # O(id) = T
    t = o[id]
    if isinstance(t, FunctionInfo):
        raise SemanticError(
            f"Function identifier `{id}' used where value identifier expected"
        )
    # O, R |- e1: T1
    t1 = check_expr(o, r, e1)
    # T1 ≤a T
    check_assignment_compatibility(t1, t)
    
    return t1

# [VAR-ASSIGN-STMT]
# O, R |- id = e1
def var_assign_stmt_rule(o: LocalEnvironment, r: Type, id: str, e1: Operation):
    # O(id) = T
    t = o[id]
    if isinstance(t, FunctionInfo):
        raise SemanticError(
            f"Function identifier `{id}' used where value identifier expected"
        )
    # O, R |- e1: T1
    t1 = check_expr(o, r, e1)
    # T1 ≤a T
    check_assignment_compatibility(t1, t)
    return t
    
# [STMT-DEF-LIST] rule
# O, R |- s1 NEWLINE s2 NEWLINE . . . sn NEWLINE
def stmt_def_list_rule(o: LocalEnvironment, r: Type, sns: List[Operation]):
    # n >= 1
    assert len(sns) >= 1
    for sn in sns:
        # O, R |- sn
        check_stmt_or_def(o, r, sn)

# [PASS] rule
# O, R |- pass
def pass_rule(o: LocalEnvironment, r: Type, op: Operation):
    assert(isinstance(op, choco_ast.Pass))

# [EXPR-STMT] rule
# O, R |- e
def expr_stmt_rule(o: LocalEnvironment, r: Type, e: Operation):
    # O, R |- e: T
    check_expr(o, r, e)

# noinspection PySimplifyBooleanCheck
# O, R |- lit: T
def literal_rules(o: LocalEnvironment, r: Type, lit: choco_ast.Literal) -> Type:
    if isinstance(lit.value, choco_ast.BoolAttr):
        # [BOOL-FALSE] rule
        if lit.value.data == False:
            return bool_type
        # [BOOL-TRUE] rule
        if lit.value.data == True:
            return bool_type
    # [NONE] rule
    if isinstance(lit.value, choco_ast.NoneAttr):
        return none_type
    # [INT] rule
    if isinstance(lit.value, choco_ast.IntegerAttr):
        return int_type
    # [STR] rule
    if isinstance(lit.value, choco_ast.StringAttr):
        return str_type
    raise Exception(f"Could not type check literal `{lit}'")

# [NEGATE] rule
# O, R, |- - e: int
def negate_rule(o: LocalEnvironment, r: Type, e: Operation) -> Type:
    # O, R, |- e: int
    check_type(check_expr(o, r, e), expected=int_type)
    return int_type

# [ARITH] rule
# O, R |- e1 op e2 : int
def arith_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    assert(isinstance(op, choco_ast.BinaryExpr)) 
    assert(op.op.data in arith_op)
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=int_type)

    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=int_type)

    return int_type

# [INT-COMPARE] rule
# O, R |- e1 cmp_op e2 : bool
def int_compare_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in cmp_op)
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=int_type)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=int_type)
    
    return bool_type

# [BOOL-COMPARE] rule
# O, R |- e1 cmp_op e2 : bool
def bool_compare_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["==", "!="])
    except:
        raise SemanticError("invalid operation on types given")
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=bool_type)
    
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=bool_type)
    
    return bool_type

# [AND] rule
# O, R |- e1 and e2 : bool
def and_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["and"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=bool_type)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=bool_type)
    
    return bool_type

# [OR] rule
# O, R |- e1 or e2 : bool
def or_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["or"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=bool_type)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=bool_type)
    
    return bool_type

# [NOT] rule
# O, R |- not e : bool
def not_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.UnaryExpr)) 
        assert(op.op.data in ["not"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t = check_expr(o, r, op.value.block._first_op)
    check_type(t, expected=bool_type)

    return bool_type

# [COND] rule
# O, R |- e1 if e0 else e2 : T1 |_| T2
def cond_rule(o: LocalEnvironment, r: Type, e1: Operation, e0: Operation, e2: Operation) -> Type:
    # O, R |- e0: bool
    check_type(check_expr(o, r, e0), expected=bool_type)
    # O, R |- e1: t1
    t1 = check_expr(o, r, e1)
    # O, R |- e2: t2
    t2 = check_expr(o, r, e2)

    return join(t1, t2)

# [STR-COMPARE] rule
# O, R |- e1 cmp_op e2 : bool
def str_compare_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr))
        assert(op.op.data in ["==", "!="])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=str_type)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=str_type)
    
    return bool_type

# [STR-CONCAT]
# O, R |- e1 + e2 : str
def str_concat_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["+"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_type(t1, expected=str_type)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_type(t2, expected=str_type)
    
    return str_type

# [STR-SELECT]
# O, R |- e1[e2] : str
def str_select_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.IndexExpr))
    except:
        raise SemanticError("unexpected operation on types given")
    
    t1 = check_expr(o, r, op.value.op)
    check_type(t1, expected=str_type)
    t2 = check_expr(o, r, op.index.op)
    check_type(t2, expected=int_type)
    
    return str_type

# [IS]
# O, R |- e1 is e2 : bool
def is_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["is"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    
    if t1 != t2 and not (isinstance(t1, ListType) and isinstance(t2, ListType)):
        if t2 == none_type:
            pass
        else:
            raise SemanticError(f"did not expect type {t1}")
        
    return bool_type

# [LIST-DISPLAY]
# O, R |- [e1, e2, ..., en] : [T] | [] : <Empty>
def list_display_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    assert(isinstance(op, choco_ast.ListExpr))
    if op.elems.blocks[0]._first_op is None:
        return empty_type
    
    list = reduce(lambda x, y: [x]+[y], \
        [[check_expr(o, r, _op) for _op in b.ops if op is not None] for b in op.elems.blocks])
    
    return ListType(reduce(lambda x, y: join(x, y), list))

# [LIST-CONCAT]
# O, R |- e1 + e2 : [T]
def list_concat_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.BinaryExpr)) 
        assert(op.op.data in ["+"])
    except:
        raise SemanticError("invalid operation on types given")
    
    t1 = check_expr(o, r, op.lhs.blocks[0]._first_op)
    check_list_type(t1)
    t2 = check_expr(o, r, op.rhs.blocks[0]._first_op)
    check_list_type(t2)
    
    return join(t1, t2)

# [LIST-SELECT]
# O, R |- e1[e2] : T
def list_select_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.IndexExpr))
    except:
        raise SemanticError("unexpected operation on types given")
    
    t1 = check_expr(o, r, op.value.op)
    check_list_type(t1)
    t2 = check_expr(o, r, op.index.op)
    check_type(t2, expected=int_type)
    
    return t1.elem_type

# [ASSIGN]
# O, R |- e1 = e2 : T
def assign_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.Assign))
    except:
        raise SemanticError("expected an assignment statement")
    if isinstance(op.value.op, choco_ast.Assign):
        return assign_multi_rule(o, r, op)
    else:
        return assign_single_rule(o, r, op)  

def assign_multi_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.Assign))
        assert(isinstance(op.value.op, choco_ast.Assign))
    except:
        raise SemanticError("expected an assignment statement")
    
    tgt = op.target.op
    value = op.value.op
    
    if not isinstance(tgt, choco_ast.IndexExpr) and not isinstance(tgt, choco_ast.ExprName):
        raise SemanticError("expected an index expression or expression name on lhs of assignment")
    
    tgt_type = check_expr(o, r, tgt)
    value_type = assign_rule(o, r, value)
    check_assignment_compatibility(value_type, tgt_type)

    return value_type  

def assign_single_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.Assign))
    except:
        raise SemanticError("expected an assignment statement")
    
    tgt = op.target.op
    value = op.value.op
    
    if not isinstance(tgt, choco_ast.IndexExpr) and not isinstance(tgt, choco_ast.ExprName):
        raise SemanticError("expected an index expression or expression name on lhs of assignment")
    
    tgt_type = check_expr(o, r, tgt)
    value_type = check_expr(o, r, value)

    check_assignment_compatibility(value_type, tgt_type)
    
    return value_type

# [INVOKE]
# O, R |- f(e1, e2, ..., en): T0
def invoke_rule(o: LocalEnvironment, r: Type, op: Operation) -> Type:
    try:
        assert(isinstance(op, choco_ast.CallExpr))
    except:
        raise SemanticError("expected a call expression")
    
    # f: T1 x T2 x ... x Tn -> T0
    f = o[op.func.data]
    if not isinstance(f, FunctionInfo):
        raise SemanticError(f"Found {f} where function expected")
    
    # O, R |- e1: T1 ...
    for i, arg in enumerate(op.args.ops):
        t = check_expr(o, r, arg)
        check_assignment_compatibility(t, f.func_type.inputs[i])
    
    return f.func_type.output

# [RETURN and RETURN-e] rule
# O, R |- return | return e: R
def return_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.Return))
    except:
        raise SemanticError("expected a return statement")
    
    t = none_type
    if op.value.block._first_op is not None:
        t = check_expr(o, r, op.value.op)
    check_type(t, r)

# [IF-ELSE]
# O, R |- if e: b1 else: b2
def if_else_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.If))
    except:
        raise SemanticError("expected an if statement")
    
    e = op.cond.op
    b1 = op.then.block.ops
    b2 = op.orelse.block.ops
    # O, R |- e: bool
    check_type(check_expr(o, r, e), expected=bool_type)
    # O, R |- b1
    check_stmt_or_def_list(o, r, list(b1))
    # O, R |- b2
    if len(b2) > 0:
        check_stmt_or_def_list(o, r, list(b2))

# [WHILE]
# O, R |- while e: b
def while_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.While))
    except:
        raise SemanticError("expected a while statement")
    
    e = op.cond.op
    b = op.body.block.ops
    # O, R |- e: bool
    check_type(check_expr(o, r, e), expected=bool_type)
    # O, R |- b1
    check_stmt_or_def_list(o, r, list(b))

# [FOR]
# O, R |- for id in e: b
def for_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.For))
    except:
        raise SemanticError("expected a for statement")
    
    # O, R |- e: [T]
    iter_type = check_expr(o, r, op.iter.op)

    if not isinstance(iter_type, ListType):
        return for_str_rule(o, r, op)
    else:
        return for_list_rule(o, r, op)
    
# [FOR-STR]
# O, R |- for id in e: b
def for_str_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.For))
    except:
        raise SemanticError("expected a for statement")
    
    # O, R |- e: str
    iter_type = check_expr(o, r, op.iter.op)
    check_type(iter_type, str_type)
    
    # check id is string
    id = op.iter_name.data
    check_type(o[id], str_type)
    
    # O, R |- b1
    b = op.body.block.ops
    check_stmt_or_def_list(o, r, list(b))

# [FOR-LIST]
# O, R |- for id in e: b
def for_list_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.For))
    except:
        raise SemanticError("expected a for statement")
    
    # O, R |- e: [T]
    iter_type = check_expr(o, r, op.iter.op)
    check_list_type(iter_type)
    
    # add id to the environment
    id = op.iter_name.data
    check_type(o[id], iter_type.elem_type)
    
    # O, R |- b1
    b = op.body.block.ops
    check_stmt_or_def_list(o, r, list(b))

# [FUNC-DEF] rule
# O, R |- def f(x1:T1, ... , xn:Tn)  [[-> T0]]? :b
def func_def_rule(o: LocalEnvironment, r: Type, op: Operation):
    try:
        assert(isinstance(op, choco_ast.FuncDef))
    except:
        raise SemanticError("expected a function definition")
    
    f_name = op.func_name.data
    f_info = o[f_name]
    f_env = o.copy()
    f_env.update(zip(f_info.params, f_info.func_type.inputs))
    f_env.update(f_info.nested_defs)
    
    return_type = Type.from_op(op.return_type.op)
    
    check_stmt_or_def_list(f_env, return_type, list(op.func_body.ops))
