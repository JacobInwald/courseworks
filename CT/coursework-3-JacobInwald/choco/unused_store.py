# type: ignore

from dataclasses import dataclass

from xdsl.dialects.builtin import IntegerAttr, ModuleOp
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


# # TODO: why doesn't this work!!!!
@dataclass
class StoreRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, store: Store, rewriter: PatternRewriter
    ) -> None:
        if isinstance(store.memloc.op, (GetAddress, IndexString)):
            return
        uses = store.memloc.uses
        store_not_loaded = True
        store_found = False
        for use in uses:
            if not store_found:
                store_found = use.operation == store
                continue
            
            if isinstance(use.operation, Store):
                break
            if isinstance(use.operation, Load):
                store_not_loaded = False
                break
                
        if store_not_loaded and store_found:
            # raise Exception(store)
            rewriter.erase_op(store)


class ChocoUnusedStoreElimination(ModulePass):
    name = "choco-unused-store-elimination"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:

        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    StoreRewriter(),
                ]
            ),
            walk_reverse=True
        )

        walker.rewrite_module(op)

