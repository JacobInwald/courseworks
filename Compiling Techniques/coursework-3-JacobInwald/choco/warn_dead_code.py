from dataclasses import dataclass
from io import StringIO

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import MLContext
from xdsl.passes import ModulePass
from xdsl.printer import Printer

from choco.ast_visitor import Visitor
from choco.dialects.choco_ast import *


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


class WarnDeadCode(ModulePass):
    name = "warn-dead-code"
    
    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        program = op.ops.first
        assert isinstance(program, Program)

        # TODO: check for dead code in `program`, and raise the corresponding exception
        # if some dead code was found.
