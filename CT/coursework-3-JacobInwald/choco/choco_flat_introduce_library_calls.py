# type: ignore

from dataclasses import dataclass

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import (
    MLContext,
)
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

from choco.dialects.choco_flat import *
from choco.dialects.choco_type import *
from choco.dialects.choco_type import ListType, bool_type, int_type, str_type
from riscv.ssa_dialect import *


@dataclass(eq=False)
class CallExprPattern(RewritePattern):
    """
    Rewrite a choco flat program into a RISCV SSA program.
    """

    ctx: MLContext

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: CallExpr, rewriter: PatternRewriter):
        if op.func_name.data == "input":
            call = CallExpr.create(
                operands=[],
                result_types=[str_type],
                properties={"func_name": StringAttr("_input")},
            )
            rewriter.replace_op(op, [call], [call.results[0]])
            return

        if op.func_name.data != "print":
            return

        if op.operands[0].type == bool_type:
            call = CallExpr.create(
                operands=op.operands,
                properties={"func_name": StringAttr("_print_bool")},
            )
            rewriter.replace_op(op, [call])
            return

        if op.operands[0].type == int_type:
            call = CallExpr.create(
                operands=op.operands,
                properties={"func_name": StringAttr("_print_int")},
            )
            rewriter.replace_op(op, [call])
            return

        if op.operands[0].type == str_type:
            call = CallExpr.create(
                operands=op.operands,
                properties={"func_name": StringAttr("_print_str")},
            )
            rewriter.replace_op(op, [call])
            return

        raise Exception(
            "Type Error: Cannot print an object of type different than bool, int, or str"
        )


@dataclass(eq=False)
class BinaryExprPattern(RewritePattern):
    """
    Rewrite certain binary expressions to function calls provides as part of
    the runtime library.
    """

    ctx: MLContext

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: BinaryExpr, rewriter: PatternRewriter):
        if op.op.data == "+" and (
            type(op.results[0].type) == ListType or op.results[0].type == str_type
        ):
            call = CallExpr.create(
                operands=op.operands,
                result_types=[op.results[0].type],
                properties={"func_name": StringAttr("_list_concat")},
            )
            rewriter.replace_op(op, [call])

        if op.op.data == "==" and op.lhs.type == str_type:
            call = CallExpr.create(
                operands=op.operands,
                result_types=[op.result.type],
                properties={"func_name": StringAttr("_str_eq")},
            )
            rewriter.replace_op(op, [call])

        if op.op.data == "!=" and op.lhs.type == str_type:
            call = CallExpr.create(
                operands=op.operands,
                result_types=[op.result.type],
                properties={"func_name": StringAttr("_str_eq")},
            )
            complement = UnaryExpr.build(
                operands=[call],
                properties={"op": StringAttr("not")},
                result_types=[op.result.type],
            )
            rewriter.replace_op(op, [call, complement])


class ChocoFlatIntroduceLibraryCalls(ModulePass):
    name = "choco-flat-introduce-library-calls"

    def apply(self, ctx: MLContext, op: ModuleOp):
        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    CallExprPattern(ctx),
                    BinaryExprPattern(ctx),
                ]
            ),
            apply_recursively=False,
        )

        walker.rewrite_module(op)
