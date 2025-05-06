from dataclasses import dataclass

from xdsl.dialects import builtin
from xdsl.ir import MLContext
from xdsl.passes import ModulePass

from choco.ast_visitor import Visitor
from choco.dialects.choco_ast import *
from choco.semantic_error import SemanticError


class CheckAssignTargetPass(ModulePass):
    name = "check-assign-target"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        """
        Check that the left-hand side of an assignment is either:
            - a variable name; or
            - an index expression.
        """

        @dataclass
        class AssignVisitor(Visitor):
            def visit_assign(self, assign: Assign):
                assert len(assign.target.blocks) == 1
                assert len(assign.target.blocks[0].ops) == 1
                target_op = assign.target.blocks[0].ops.first
                if isinstance(target_op, ExprName):
                    return
                if isinstance(target_op, IndexExpr):
                    return
                raise SemanticError(
                    f"Found {type(target_op).__name__} as the left-hand side of an assignment. "
                    f"Expected to find variable name or index expression only."
                )

        visitor = AssignVisitor()
        visitor.traverse(op)
