from dataclasses import dataclass

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import MLContext
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


class AllocRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, alloc: Alloc, rewriter: PatternRewriter
    ) -> None:
        if len(alloc.memloc.uses) == 0:
            rewriter.erase_op(alloc)
        return

@dataclass
class StoreRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, store: Store, rewriter: PatternRewriter
    ) -> None:
        get_address = isinstance(store.memloc.op, (GetAddress, IndexString))
        if get_address:
            return
        
        uses = store.memloc.uses
        all_stores = all([isinstance(use.operation, Store) for use in uses])
        
        if all_stores or len(uses) == 0:
            rewriter.erase_op(store)

@dataclass
class LoadRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(self, load: Load, rewriter: PatternRewriter) -> None:

        if len(load.result.uses) == 0 or \
            len(load.results[0].uses) == 0:
            rewriter.replace_op(load, [], [None])
        return

@dataclass
class LiteralRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, literal: Literal, rewriter: PatternRewriter
    ) -> None:
        if len(literal.results[0].uses) == 0:
            rewriter.replace_op(literal, [], [None])
        return


@dataclass
class BinaryExprRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: BinaryExpr, rewriter: PatternRewriter
    ) -> None:
        if expr.op.data == "//":
            return
        if len(expr.results[0].uses) == 0:
            rewriter.replace_op(expr, [], [None])
        return


class OperationRewriter:
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: Operation, rewriter: PatternRewriter
    ) -> None:
        if isinstance(expr, (ModuleOp, EffectfulBinaryExpr, IfExpr, CallExpr, \
                                Alloc, Store, Load, Literal, BinaryExpr)):
            return
        if len(expr.results) > 0 and \
            len(expr.results[0].uses) == 0 and\
            not isinstance(expr, (ModuleOp, EffectfulBinaryExpr, IfExpr, CallExpr)):
            rewriter.erase_op(expr)
        return

class ChocoFlatDeadCodeElimination(ModulePass):
    name = "choco-flat-dead-code-elimination"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    LiteralRewriter(),
                    BinaryExprRewriter(),
                    StoreRewriter(),
                    LoadRewriter(),
                    OperationRewriter(),
                    AllocRewriter(),
                ]
            ),
            walk_reverse=True,
        )
        walker.rewrite_module(op)
        return
