from dataclasses import dataclass
from typing import Dict

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
from util.list_ops import *

@dataclass
class LiteralRewriter(RewritePattern):
    encountered_lits = {}
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, literal: Literal, rewriter: PatternRewriter
    ) -> None:
        encountered = self.encountered_lits.get(str(literal.value), None) is not None
        
        if encountered:
            rewriter.replace_matched_op([], [self.encountered_lits[str(literal.value)].result])
        else:
            self.encountered_lits[str(literal.value)] = literal


class ChocoFlatDupeElimination(ModulePass):
    name = "choco-flat-dupe-elimination"
     
    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        main = None
        ops = flatten([[o for o in block.ops] for block in op.body.blocks])
        for _op in ops:
            if isinstance(_op, FuncDef) and \
                _op.func_name.data == "_main":
                main = _op
        if main is None:
            raise Exception("No main function found")
        
        lit = LiteralRewriter()
        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    lit,
                ]
            ),
            walk_reverse=False,
        )
        walker.rewrite_module(op)

        for k, v in lit.encountered_lits.items():
            new = v.clone()
            v.results[0].replace_by(new.results[0])
            v.detach()
            v.erase()
            main.func_body.blocks[0].insert_op_before(new, main.func_body.blocks[0].first_op)
