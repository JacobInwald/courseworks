from dataclasses import dataclass
from io import StringIO

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import MLContext
from xdsl.passes import ModulePass
from xdsl.printer import Printer

from choco.ast_visitor import Visitor
from choco.dialects.choco_ast import *

from typing import Dict
from enum import Enum 

class DeadCodeError(Exception):
    pass


@dataclass
class UnreachableStatementsError(DeadCodeError):
    """Raised when some statements are unreachable."""

    def __str__(self) -> str:
        return "Program contains unreachable statements."


@dataclass
class UnreachableExpressionError(DeadCodeError):
    """Raised when parts of an expression is unreachable."""

    def __str__(self) -> str:
        return "Program contains unreachable expressions."


@dataclass
class UnusedStoreError(DeadCodeError):
    """Raised when a store operation is unused."""

    op: Assign

    def __str__(self) -> str:
        stream = StringIO()
        printer = Printer(stream=stream)
        print("The following store operation is unused: ", file=stream)
        printer.print_op(self.op)
        return stream.getvalue()


@dataclass
class UnusedVariableError(DeadCodeError):
    """Raised when a variable is unused."""

    name: str

    def __str__(self) -> str:
        return f"The following variable is unused: {self.name}."


@dataclass
class UnusedArgumentError(DeadCodeError):
    """Raised when a function argument is unused."""

    name: str

    def __str__(self) -> str:
        return f"The following function argument is unused: {self.name}."


@dataclass
class UnusedFunctionError(DeadCodeError):
    """Raised when a function is unused."""

    name: str

    def __str__(self) -> str:
        return f"The following function is unused: {self.name}."


@dataclass
class UnusedExpressionError(DeadCodeError):
    """Raised when the result of an expression is unused."""

    expr: Operation

    def __str__(self) -> str:
        stream = StringIO()
        printer = Printer(stream=stream)
        print("The following expression is unused: ", file=stream)
        printer.print_op(self.expr)
        return stream.getvalue()

class NameType(Enum):
    USED_ARGUMENT = 1
    USED_VARIABLE = 2
    USED_FUNCTION = 3
    USED_VARIABLE_IN_ASSIGN = 4
    UNUSED_ARGUMENT = 5
    UNUSED_VARIABLE = 6
    UNUSED_FUNCTION = 7


RETURN = 0
Env = Dict[str, Operation]
UsedEnv = Dict[str, NameType]
AssignEnv = Dict[str, Assign]

class WarnDeadCode(ModulePass):
    name = "warn-dead-code"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        self.env: Env = {}
        self.used: UsedEnv = {}
        self.last_store: AssignEnv = {}
        program = op.ops.first
        assert isinstance(program, Program)

        defs = list(program.defs.ops)
        if len(defs) >= 1:
            self.check_stmt_or_def_list(self.used, defs)
            
        stmts = list(program.stmts.ops)
        if len(stmts) >= 1:
            self.check_stmt_or_def_list(self.used, stmts)
        
        for k, v in self.used.items():
            if v == NameType.UNUSED_VARIABLE:
                raise UnusedVariableError(k)
            elif v == NameType.UNUSED_FUNCTION:
                raise UnusedFunctionError(k)
            elif v == NameType.UNUSED_ARGUMENT:
                raise UnusedArgumentError(k)

    def check_literal(self, op: Operation, expected: Literal):
        return self.parse_simple_expr(op) == self.parse_simple_expr(expected)
    
    def parse_simple_expr(self, op: Operation):
        if not isinstance(op, Operation):
            return op
        # Base Case
        if isinstance(op, Literal):
            if isinstance(op.value, IntegerAttr):
                return op.value.value
            return op.value.data
        elif isinstance(op, ExprName):
            op = self.env.get(op.id.data)
            if isinstance(op, (Literal, IntegerAttr)):
                return self.parse_simple_expr(op)
            return op
        # Unary Expression
        elif isinstance(op, UnaryExpr):
            if op.op.data == "not":
                return not self.parse_simple_expr(op.value.op)
            elif op.op.data == "-":
                return - self.parse_simple_expr(op.value.op)
        # Binary Expression
        elif isinstance(op, BinaryExpr):
            # Get the value of the sides
            lhs = op.lhs.op
            rhs = op.rhs.op
            if isinstance(op.lhs.op, ExprName):
                lhs = self.env.get(op.lhs.op.id.data)
            if isinstance(op.rhs.op, ExprName):
                rhs = self.env.get(op.rhs.op.id.data)
            lhs = self.parse_simple_expr(lhs)
            rhs = self.parse_simple_expr(rhs)
            # Ensure that the values are not None
            if lhs is None or rhs is None:
                    return
            # Parse the operations
            if op.op.data in ["and"]:
                if lhs == False:
                    raise UnreachableExpressionError()
                return lhs and rhs
            elif op.op.data in ["or"]:
                if lhs == True:
                    raise UnreachableExpressionError()
                return lhs or rhs
            elif op.op.data in ["=="]:
                return lhs == rhs
            elif op.op.data in ["!="]:
                return lhs != rhs
            elif op.op.data in ["<"]:
                return lhs < rhs
            elif op.op.data in ["<="]:
                return lhs <= rhs
            elif op.op.data in [">"]:
                return lhs > rhs
            elif op.op.data in [">="]:
                return lhs >= rhs
            elif op.op.data in ["+"]:
                return lhs + rhs
            elif op.op.data in ["-"]:
                return lhs - rhs
            elif op.op.data in ["*"]:
                return lhs * rhs
            elif op.op.data in ["//"]:
                return lhs // rhs
            elif op.op.data in ["%"]:
                return lhs % rhs
            elif op.op.data in ["/"]:
                return lhs / rhs
        # If Expression
        elif isinstance(op, IfExpr):
            cond = op.cond.op
            then = op.then.op
            or_else = op.or_else.op
            if self.check_literal(cond, Literal(True)) or self.check_literal(cond, Literal(False)):
                raise UnreachableExpressionError()
            self.parse_simple_expr(then)
            self.parse_simple_expr(or_else)
        return None
    
    def assign_env(self, id, op: Operation):
        self.env[id] = self.parse_simple_expr(op)
    
    def check_stmt_or_def_list(self, u: UsedEnv, ops: List[Operation]):
        assert len(ops) >= 1
        
        for i in range(len(ops)):
            op = ops[i]
            if self.check_stmt_or_def(u, op) == RETURN and i < len(ops) - 1:
                raise UnreachableStatementsError()

    def check_stmt_or_def(self, u: UsedEnv, op: Operation):
        if isinstance(op, VarDef):
            u[op.typed_var.op.var_name.data] = NameType.UNUSED_VARIABLE
            self.env[op.typed_var.op.var_name.data] = op.literal.op
        elif isinstance(op, Assign):
            return self.check_assign(u, op)
        elif isinstance(op, Pass):
            return
        elif isinstance(op, Return):
            if op.value is not None:
                self.check_expr(u, op.value.block._first_op)
            return RETURN
        elif isinstance(op, If):
            return self.check_if(u, op)
        elif isinstance(op, While):
            return self.check_while(u, op)
        elif isinstance(op, For):
            return self.check_for(u, op)
        elif isinstance(op, FuncDef):
            u[op.func_name.data] = NameType.UNUSED_FUNCTION
            return self.check_func_def(u, op)
        elif isinstance(op, GlobalDecl):
            self.used[op.decl_name.data] = NameType.USED_VARIABLE
            return
        elif isinstance(op, NonLocalDecl):
            return
        elif isinstance(op, CallExpr):
            return self.check_expr(u, op)
        else:
            raise UnusedExpressionError(op)

    def check_expr(self, u: UsedEnv, op: Operation) -> Type:
        if isinstance(op, Literal):
            return
        elif isinstance(op, ExprName):
            u[op.id.data] = NameType.USED_VARIABLE
        elif isinstance(op, UnaryExpr):
            return self.check_expr(u, op.value.op)
        elif isinstance(op, BinaryExpr):
            return self.check_binary_expr(u, op)
        elif isinstance(op, IfExpr):
            return self.check_if_expr(u, op)
        elif isinstance(op, IndexExpr):
            self.check_expr(u, op.index.op)
            self.check_expr(u, op.value.op)
        elif isinstance(op, ListExpr):
            for _op in op.elems.ops:
                self.check_expr(u, _op)
        elif isinstance(op, CallExpr):
            u[op.func.data] = NameType.USED_FUNCTION
            return self.check_call_expr(u, op)

    def check_assign(self, u: UsedEnv, op: Assign):
        
        # Check if the variable is used in the assignment
        tgt = op.target.op
        val = op.value.op
        self.check_expr(u, op.value.op)
        if isinstance(val, Assign):
            self.check_assign(u, val)
        elif isinstance(tgt, ExprName):
            self.assign_env(tgt.id.data, op.value.op)
            # Variable hasn't been used since the last assignment
            if u[tgt.id.data] == NameType.USED_VARIABLE_IN_ASSIGN:
                raise UnusedStoreError(self.last_store[tgt.id.data])
            # Variable is used in the assignment, so it's not unused, but it s
            u[tgt.id.data] = NameType.USED_VARIABLE_IN_ASSIGN
            self.last_store[tgt.id.data] = op
            
        elif isinstance(tgt, IndexExpr) and isinstance(tgt.value.op, ExprName):
            id = tgt.value.op.id.data
            # catches dead assigns of form x[0] = 1, x[0] = 2
            if isinstance(tgt.index.op, Literal):
                id = id + "[" + str(tgt.index.op.value) + "]"
                
                if u.get(id) == NameType.USED_VARIABLE_IN_ASSIGN:
                    raise UnusedStoreError(self.last_store[id])
                
                # Variable is used in the assignment, so it's not unused, but it s
                u[id] = NameType.USED_VARIABLE_IN_ASSIGN
                self.last_store[id] = op
                u[id] = NameType.USED_VARIABLE_IN_ASSIGN
            else:
                u[id] = NameType.USED_VARIABLE
                      
    def check_if(self, u: UsedEnv, op: If):
        if self.check_literal(op.cond.op, Literal(False)):
            raise UnreachableStatementsError()
        self.check_expr(u, op.cond)
        self.check_stmt_or_def_list(u, list(op.then.ops))
        if len(op.orelse.ops) >= 1:
            if self.check_literal(op.cond, Literal(True)):
                raise UnreachableStatementsError()
            self.check_stmt_or_def_list(u, list(op.orelse.ops))

    def check_if_expr(self, u: UsedEnv, op: IfExpr):  
        if self.check_literal(op.cond.op, Literal(False)) or \
            self.check_literal(op.cond.op, Literal(True)):
            raise UnreachableExpressionError()
        self.check_expr(u, op.cond)
        self.check_expr(u, op.then.op)
        self.check_expr(u, op.or_else.op)
        
    def check_while(self, u: UsedEnv, op: While):
        if self.check_literal(op.cond.op, Literal(False)):
            raise UnreachableStatementsError()
        self.check_expr(u, op.cond)
        self.check_stmt_or_def_list(u, list(op.body.ops))
        
    def check_for(self, u: UsedEnv, op: For):
        if isinstance(op.iter, ListExpr) and len(op.iter.elems.ops) == 0:
            raise UnreachableStatementsError()
        
        u[op.iter_name.data] = NameType.USED_VARIABLE
        self.check_expr(u, op.iter.op)
        self.check_stmt_or_def_list(u, list(op.body.ops))

    def check_func_def(self, u: UsedEnv, op: FuncDef):
        f_u = u.copy()
        for arg in op.params.ops:
            assert isinstance(arg, TypedVar)
            f_u[arg.var_name.data] = NameType.UNUSED_ARGUMENT
        
        saved = self.env.copy()
        self.check_stmt_or_def_list(f_u, list(op.func_body.ops))
        self.env = saved
        
        for k, v in f_u.items():
            if v == NameType.UNUSED_ARGUMENT:
                raise UnusedArgumentError(k)

    def check_call_expr(self, u: UsedEnv, op: CallExpr):
        for _op in op.args.ops:
            self.check_expr(u, _op)
            
    def check_binary_expr(self, u: UsedEnv, op: BinaryExpr):
        # Unreachable Logical Expressions
        if op.op.data == "and" and self.check_literal(op.lhs.op, Literal(False)):
            raise UnreachableExpressionError()
        elif op.op.data == "or" and self.check_literal(op.lhs.op, Literal(True)):
            raise UnreachableExpressionError()
        
        self.check_expr(u, op.lhs.op)
        self.check_expr(u, op.rhs.op)