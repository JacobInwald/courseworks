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

def apply_str_op(op: str, e1, e2):
    if op == "+":
        return e1 + e2
    elif op == "-":
        return e1 - e2
    elif op == "*":
        return e1 * e2
    elif op == "//":
        return e1 // e2
    elif op == "%":
        return e1 % e2
    elif op == "==":
        return e1 == e2
    elif op == "!=":
        return e1 != e2
    elif op == "<":
        return e1 < e2
    elif op == ">":
        return e1 > e2
    elif op == "<=":
        return e1 <= e2
    elif op == ">=":
        return e1 >= e2
    elif op == "is":
        return e1 is e2
    elif op == "and":
        return e1 and e2
    elif op == "or":
        return e1 or e2
    else:
        raise ValueError(f"Unknown operator: {op}")


# # TODO: why doesn't this work!!!!
# @dataclass
# class StoreLoadRewriter(RewritePattern):
#     encountered_stores  = {}
    
#     @op_type_rewrite_pattern
#     def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
#         self, op: Union[Store, Load, For], rewriter: PatternRewriter
#     ) -> None:
#         if isinstance(op, Store):
#             self.match_and_rewrite_store(op, rewriter)
#         elif isinstance(op, Load):
#             self.match_and_rewrite_load(op, rewriter)
#         else:
#             self.match_and_rewrite_for(op, rewriter)
    
#     def match_and_rewrite_for(self, for_: For, rewriter: PatternRewriter) -> None:
#         self.encountered_stores.pop(hash(for_.iter_), None) 

#     def match_and_rewrite_store(self, store: Store, rewriter: PatternRewriter) -> None:
#         self.encountered_stores.pop(hash(store.memloc), None)
#         if isinstance(store.value, OpResult) and \
#             isinstance(store.value.op, Literal) and \
#             (store.value.op.results[0].type == int_type or \
#             store.value.op.results[0].type == bool_type):
#             self.encountered_stores[hash(store.memloc)] = store   

#     def match_and_rewrite_load(self, load: Load, rewriter: PatternRewriter) -> None:
#         encountered = self.encountered_stores.get(hash(load.memloc), None) is not None
#         if encountered:
#             prev_store = self.encountered_stores[hash(load.memloc)]
#             # rewriter.replace_matched_op([], [prev_store.value.op.results[0]])
   
    
@dataclass
class BinaryExprRewriter(RewritePattern):
    def is_integer_literal(self, op: Operation):
        return isinstance(op, Literal) and isinstance(op.value, IntegerAttr)

    def is_boolean_literal(self, op: Operation):
        return isinstance(op, Literal) and isinstance(op.value, BoolAttr)
    
    def order_sides(self, expr: BinaryExpr):
        order = {}
        lhs = expr.lhs.op
        rhs = expr.rhs.op
        if isinstance(lhs, BinaryExpr):
            order[0] = lhs.lhs.op
            order[1] = lhs.rhs.op
        else:
            order[0] = lhs
        max_order = max(order.keys())
        if isinstance(rhs, BinaryExpr):
            order[max_order+1] = rhs.lhs.op
            order[max_order+2] = rhs.rhs.op
        else:
            order[max_order+1] = rhs
        return order
    
    def rewrite_constant_op(self, expr: BinaryExpr, rewriter: PatternRewriter):
        if self.is_integer_literal(expr.lhs.op) and self.is_integer_literal(expr.rhs.op):
            lhs_value = expr.lhs.op.value.parameters[0].data
            rhs_value = expr.rhs.op.value.parameters[0].data
        elif self.is_boolean_literal(expr.lhs.op) and self.is_boolean_literal(expr.rhs.op):
            lhs_value = expr.lhs.op.value.data
            rhs_value = expr.rhs.op.value.data
        else:
            return
        result_value = apply_str_op(expr.op.data, lhs_value, rhs_value)
        new_constant = Literal.get(result_value)
        rewriter.replace_matched_op([new_constant], [new_constant.result])
        
    def rewrite_constant_var_op(self, expr: BinaryExpr, rewriter: PatternRewriter):
        if not (self.is_integer_literal(expr.lhs.op) ^ self.is_integer_literal(expr.rhs.op)):
            return
        
        constant = expr.lhs.op if self.is_integer_literal(expr.lhs.op) else expr.rhs.op
        other: Operation = expr.lhs.op if self.is_integer_literal(expr.rhs.op) else expr.rhs.op
        
        # ? Case for 0 op x OR x op 0
        if constant.value.parameters[0].data == 0:
            if expr.op.data == "+":
                rewriter.replace_matched_op([other.clone()])
            elif expr.op.data == "-":
                if constant == expr.lhs.op:
                    rewriter.replace_matched_op([UnaryExpr.get("-", [other.clone()])])
                else:
                    rewriter.replace_matched_op([other.clone()])
            elif expr.op.data == "*":
                rewriter.replace_matched_op([Literal.get(0)])
            elif expr.op.data == "//":
                if constant == expr.lhs.op:
                    rewriter.replace_matched_op([Literal.get(0)])
            elif expr.op.data == "%":
                if constant == expr.lhs.op:
                    rewriter.replace_matched_op([Literal.get(0)])
        # ? Case for 1 op x OR x op 1
        elif constant.value.parameters[0].data == 1:
            if expr.op.data == "*":
                rewriter.replace_op(expr, [other.clone()])
            elif expr.op.data == "//":
                if constant == expr.rhs.op:
                    rewriter.replace_op(expr, [other.clone()])
            elif expr.op.data == "%":
                if constant == expr.rhs.op:
                    rewriter.replace_matched_op([Literal.get(0)])

    #! Associativity Folding
    def bubble_constants_pure(self, expr: BinaryExpr, rewriter: PatternRewriter):
        order = self.order_sides(expr)
        pure = all([e.op.data==expr.op.data \
            for e in [expr, expr.rhs.op, expr.lhs.op] \
                if isinstance(e, BinaryExpr)])
        if len(order.items()) != 3 or \
            expr.op.data not in ["+", "*", "//", "-", "%"] or \
            not pure:
            return
        
        types = {}
        results = {}
        for i, v in enumerate(order.values()):
            types[i] = isinstance(v, Literal) or \
                (isinstance(v, OpResult) and isinstance(v.op, Literal))
            results[i] = v if isinstance(v, OpResult) else v.results[0]
            
        
        if isinstance(expr.lhs.op, BinaryExpr) and \
            expr.op.data == "%" and types[1] and types[2]:
            n_l = results[0]
            if order[1].value.parameters[0].data > order[2].value.parameters[0].data:
                n_r = results[2]
                n_rr = order[1]
            else:
                n_r = results[1]
                n_rr = order[2]
            new_op = BinaryExpr.create(
                    properties={"op": StringAttr("%")},
                    operands=[n_l, n_r],
                    result_types=[n_l.type],
                )
            rewriter.replace_matched_op([new_op], [new_op.result])
            return

        
        n_lhs_op = expr.op.data
        n_op = expr.op.data
        num_c = len([v for v in types.values() if v]) 
        flip_op = lambda x: "*" if x == "//" else ("+" if x == "-" else x)
        
        if isinstance(expr.lhs.op, BinaryExpr) and \
                ((types[1] and num_c == 2) or \
                (not types[1] and num_c == 1)):
            n_lhs_op = flip_op(n_lhs_op)
            n_l = results[1]
            n_r = results[2]
            n_rr = results[0]
        elif isinstance(expr.lhs.op, BinaryExpr) and \
                ((types[0] and num_c == 2) or \
                (not types[0] and num_c == 1)):
            n_l = results[0]
            n_r = results[2]
            n_rr = results[1] 
        elif isinstance(expr.rhs.op, BinaryExpr) and \
                ((types[1] and num_c == 2) or \
                (not types[1] and num_c == 1)):
            n_op = flip_op(n_op)
            n_l = results[0]
            n_r = results[1]
            n_rr = results[2]
        elif isinstance(expr.rhs.op, BinaryExpr) and \
                ((types[2] and num_c == 2) or \
                (not types[2] and num_c == 1)):
            n_lhs_op = flip_op(n_lhs_op)
            n_l = results[0]
            n_r = results[2]
            n_rr = results[1]
        else:
            return

        n_lhs = BinaryExpr.create(
            properties={"op": StringAttr(n_lhs_op)},
            operands=[n_l, n_r],
            result_types=[n_l.type],
        )
        
        new_op = BinaryExpr.create(
            properties={"op": StringAttr(n_op)},
            operands=[n_lhs.result, n_rr],
            result_types=[n_lhs.result.type],
        )

        rewriter.replace_matched_op([n_lhs, new_op], [new_op.result])

    #! Distributivity Folding
    def bubble_constants_impure(self, expr: BinaryExpr, rewriter: PatternRewriter):
        order = self.order_sides(expr)
        bin_op = expr.lhs.op if isinstance(expr.lhs.op, BinaryExpr) else expr.rhs.op
        
        if len(order.items()) != 3 or \
                expr.op.data not in ["+", "-"]:
            return
        if not (bin_op.op.data == "+" and expr.op.data == "-" or \
            bin_op.op.data == "-" and expr.op.data == "+"):
                return
        
        types = {}
        results = {}
        for i, v in enumerate(order.values()):
            types[i] = isinstance(v, Literal) or \
                (isinstance(v, OpResult) and isinstance(v.op, Literal))
            results[i] = v if isinstance(v, OpResult) else v.results[0]
            

        n_lhs_op = bin_op.op.data
        n_op = expr.op.data
        num_c = len([v for v in types.values() if v]) 
        
        
        # (x + a) - b -> (a - b) + x
        # (x - a) + b -> (b - a) + x
        if isinstance(expr.lhs.op, BinaryExpr) and \
                ((types[1] and num_c == 2) or \
                (not types[1] and num_c == 1)):
            n_lhs_op = "-"
            n_op = "+"
            n_l = results[1] if bin_op.op.data == "+" else results[2]
            n_r = results[2] if bin_op.op.data == "+" else results[1]
            n_rr = results[0]
        # (a + x) - b -> (a - b) + x
        # (a - x) + b -> (a + b) - x
        elif isinstance(expr.lhs.op, BinaryExpr) and \
                ((types[0] and num_c == 2) or \
                (not types[0] and num_c == 1)):
            n_lhs_op = expr.op.data
            n_op = bin_op.op.data
            n_l = results[0]
            n_r = results[2]
            n_rr = results[1] 
        # a - (b + x) -> (a - b) - x
        # a + (b - x) -> (a + b) - x
        elif isinstance(expr.rhs.op, BinaryExpr) and \
                ((types[1] and num_c == 2) or \
                (not types[1] and num_c == 1)):
            n_lhs_op = n_op
            n_op = "-"
            n_l = results[0]
            n_r = results[1]
            n_rr = results[2]
        # a - (x + b) -> (a - b) - x
        # a + (x - b) -> (a - b) + x
        elif isinstance(expr.rhs.op, BinaryExpr) and \
                ((types[2] and num_c == 2) or \
                (not types[2] and num_c == 1)):
            n_lhs_op = "-"
            n_op = expr.op.data
            n_l = results[0]
            n_r = results[2]
            n_rr = results[1]
        else:
            return

        n_lhs = BinaryExpr.create(
            properties={"op": StringAttr(n_lhs_op)},
            operands=[n_l, n_r],
            result_types=[n_l.type],
        )
        
        new_op = BinaryExpr.create(
            properties={"op": StringAttr(n_op)},
            operands=[n_lhs.result, n_rr],
            result_types=[n_lhs.result.type],
        )

        rewriter.replace_matched_op([n_lhs, new_op], [new_op.result])

    
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: BinaryExpr, rewriter: PatternRewriter
    ) -> None:

        self.rewrite_constant_op(expr, rewriter)
        self.rewrite_constant_var_op(expr, rewriter)
        
        if expr.parent is None:
            return
        
        # TODO: Simplify associative operations - X
        self.bubble_constants_pure(expr, rewriter)
        
        # TODO: Distributive Laws - X
        self.bubble_constants_impure(expr, rewriter)


@dataclass
class UnaryExprRewriter(RewritePattern):
    def is_integer_literal(self, op: Operation):
        return isinstance(op, Literal) and isinstance(op.value, IntegerAttr)

    def is_boolean_literal(self, op: Operation):
        return isinstance(op, Literal) and isinstance(op.value, BoolAttr)

    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: UnaryExpr, rewriter: PatternRewriter
    ) -> None:
        operand = expr.value
        if isinstance(operand, OpResult):
            operand = operand.op
            
        if isinstance(operand, Literal):
            if isinstance(operand.value, IntegerAttr):
                operand_value = operand.value.parameters[0].data
            elif isinstance(operand.value, BoolAttr):
                operand_value = operand.value.data
            else:
                return
            
            if expr.op.data == '-':
                new_constant = Literal.get(-operand_value)
            elif expr.op.data == 'not':
                new_constant = Literal.get(not operand_value)
            else:
                return
            rewriter.replace_op(expr, [new_constant])
            
            
@dataclass
class IfExprRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: IfExpr, rewriter: PatternRewriter
    ) -> None:
        cond = expr.cond
        if isinstance(cond, OpResult):
            cond = cond.op
            
        if isinstance(cond, Literal) and isinstance(cond.value, BoolAttr):
            cond_value = cond.value.data
            
            block = expr.then.block if cond_value else expr.or_else.block
            res: Yield = block._last_op    
            
            rewriter.inline_block_before_matched_op(block)
            rewriter.replace_matched_op([], [res.value])


@dataclass
class AndExprRewriter(RewritePattern):
        
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: EffectfulBinaryExpr, rewriter: PatternRewriter
    ) -> None:
        if expr.op.data != "and":
            return
        lhs = expr.lhs.block._last_op.value
        if isinstance(lhs, OpResult):
            lhs = lhs.op
            
        if isinstance(lhs, Literal) and  isinstance(lhs.value, BoolAttr):
            lhs_value = lhs.value.data
            if lhs_value is False:
                block = expr.lhs.block
                res: Yield = block._last_op    

                rewriter.inline_block_before_matched_op(block)
                rewriter.replace_matched_op([], [res.value])

  
@dataclass            
class OrExprRewriter(RewritePattern):
        
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: EffectfulBinaryExpr, rewriter: PatternRewriter
    ) -> None:
        if expr.op.data != "or":
            return
        lhs = expr.lhs.block._last_op.value
        if isinstance(lhs, OpResult):
            lhs = lhs.op
            
        if isinstance(lhs, Literal) and  isinstance(lhs.value, BoolAttr):
            lhs_value = lhs.value.data
            if lhs_value is True:
                block = expr.lhs.block
                res: Yield = block._last_op    
                
                rewriter.inline_block_before_matched_op(block)
                rewriter.replace_matched_op([], [res.value])
                

@dataclass
class IfRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: If, rewriter: PatternRewriter
    ) -> None:
        cond = expr.cond
        if isinstance(cond, OpResult):
            cond = cond.op
            
        if isinstance(cond, Literal) and isinstance(cond.value, BoolAttr):
            cond_value = cond.value.data
            
            block = expr.then.block if cond_value else expr.orelse.block
            rewriter.inline_block_before_matched_op(block)
            rewriter.replace_matched_op([])


@dataclass
class WhileRewriter(RewritePattern):
    
    @op_type_rewrite_pattern
    def match_and_rewrite(  # type: ignore reportIncompatibleMethodOverride
        self, expr: While, rewriter: PatternRewriter
    ) -> None:
        cond = expr.cond.block._last_op.value
        if isinstance(cond, OpResult):
            cond = cond.op
            


class ChocoFlatConstantFolding(ModulePass):
    name = "choco-flat-constant-folding"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:

        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    UnaryExprRewriter(),
                    IfExprRewriter(),
                    BinaryExprRewriter(),
                    AndExprRewriter(),
                    OrExprRewriter(),
                    IfRewriter(),
                    WhileRewriter(),
                ]
            )
        )

        walker.rewrite_module(op)
