# type: ignore

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import (
    MLContext,
    Block,
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
from riscv.ssa_dialect import *

cur_imm: LIOp = None

def def_imm(imm) -> Operation:
    global cur_imm
    
    if cur_imm is None or \
        cur_imm.immediate.value.data != imm:
        constant = LIOp(imm)
        cur_imm = constant
        return constant, True
    return cur_imm, False

def reset_imm():
    global cur_imm
    cur_imm = None


class LiteralPattern(RewritePattern):

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: Literal, rewriter: PatternRewriter):
        value = op.value
        if isinstance(value, IntegerAttr):
            constant = LIOp(value.parameters[0].data)
            rewriter.replace_matched_op(constant)
        elif isinstance(value, BoolAttr):
            constant = LIOp(1 if value.data else 0)
            rewriter.replace_op(op, [constant])
        elif isinstance(value, NoneAttr):
            constant = LIOp(0)
            rewriter.replace_op(op, [constant])
        elif isinstance(value, StringAttr):
            string = value.data

            # Constants
            size = LIOp(len(string) * 4 + 4)
            length = LIOp(len(string))
            
            # Malloc
            res = CallOp("_malloc", size)
            
            # List initialise
            s_len = SWOp(length, res.result, 0)
            ops = [size, length, res, s_len]
            for i in range(len(string)):
                char = LIOp(ord(string[i]))
                ops.append(char)
                ops.append(SWOp(char, res.result, 4*(i+1)))

            rewriter.replace_matched_op(ops, [res.result])


class CallPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: CallExpr, rewriter: PatternRewriter):
        if op.func_name.data == "len":
            zero = LIOp(0)
            maybe_fail = BEQOp(op.args[0], zero, f"_error_len_none")
            read_size = LWOp(op.args[0], 0)
            rewriter.replace_op(op, [zero, maybe_fail, read_size])
            return

        call = CallOp(op.func_name, op.args, has_result=bool(len(op.results)))
        rewriter.replace_op(op, [call])


class AllocPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, alloc_op: Alloc, rewriter: PatternRewriter):
        res = AllocOp()
        rewriter.replace_matched_op(res, [res.rd])


class StorePattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, store_op: Store, rewriter: PatternRewriter):
        address = store_op.memloc
        value = store_op.value
        store = SWOp(value, address, 0)
        rewriter.replace_op(store_op, [store])


class LoadPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, load_op: Load, rewriter: PatternRewriter):
        address = load_op.memloc
        load = LWOp(address, 0)
        rewriter.replace_matched_op([load], [load.rd])


class UnaryExprPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, unary_op: UnaryExpr, rewriter: PatternRewriter):
        op = unary_op.op.data
        e = unary_op.value
        
        if op == "not":
            not_ = SLTIUOp(e, 1)
            rewriter.replace_op(unary_op, [not_])
        elif op == "-":
            zero = LIOp(0)
            sub = SubOp(zero, e)
            rewriter.replace_op(unary_op, [zero, sub])
        else:
            raise NotImplementedError(f'UnaryExprPattern: {op} {e}')


class BinaryExprPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, bin_op: BinaryExpr, rewriter: PatternRewriter):
        lhs = bin_op.lhs
        rhs = bin_op.rhs

        self._bin_op(bin_op, rewriter)
        # if isinstance(lhs.type, RegisterType) and isinstance(rhs.type, RegisterType):
        # else:
        #     raise NotImplementedError(f'BinaryExprPattern (type not supported): {bin_op, None} {rhs.type}')
        #     raise NotImplementedError(f'BinaryExprPattern (type not recognised): {lhs.type}')

    def _bin_op(self, bin_op: BinaryExpr, rewriter: PatternRewriter):
        op = bin_op.op.data
        lhs = bin_op.lhs
        rhs = bin_op.rhs
        if op == "+":
            add = AddOp(lhs, rhs)
            rewriter.replace_op(bin_op, [add])
        elif op == "-":
            sub = SubOp(lhs, rhs)
            rewriter.replace_op(bin_op, [sub])
        elif op == "*":
            mul = MULOp(lhs, rhs)
            rewriter.replace_op(bin_op, [mul])
        elif op == "//":
            zero = LIOp(0)
            zero_check = BEQOp(rhs, zero, f"_error_div_zero")
            div = DIVOp(lhs, rhs)
            rewriter.replace_op(bin_op, [zero, zero_check, div])
        elif op == "%":
            zero = LIOp(0)
            zero_check = BEQOp(rhs, zero, f"_error_div_zero")
            rem = REMOp(lhs, rhs)
            rewriter.replace_op(bin_op, [zero, zero_check, rem])
        elif op == "<":
            lt = SLTOp(lhs, rhs)
            rewriter.replace_op(bin_op, [lt])
        elif op == ">":
            gt = SLTOp(rhs, lhs)
            rewriter.replace_op(bin_op, [gt])
        elif op == "<=":
            gt = SLTOp(rhs, lhs)
            negate = XORIOp(gt, 1)
            rewriter.replace_op(bin_op, [gt, negate])
        elif op == ">=":
            lt = SLTOp(lhs, rhs)
            negate = XORIOp(lt, 1)
            rewriter.replace_op(bin_op, [lt, negate])
        elif op == "==":
            xor = XOROp(lhs, rhs) # XOR is != to
            eq = SLTIUOp(xor, 1) # SEQZ(xor)
            rewriter.replace_op(bin_op, [xor, eq])
        elif op == "!=":
            xor = XOROp(lhs, rhs) # XOR is != to
            zero = LIOp(0) # Need to cleanup the value though
            neq = SLTUOp(zero, xor)
            rewriter.replace_op(bin_op, [xor, zero, neq])
        elif op == "is": # TODO: how to compare addresses
            xor = XOROp(lhs, rhs) # XOR is != to
            eq = SLTIUOp(xor, 1) # SEQZ(xor)
            rewriter.replace_op(bin_op, [xor, eq])
        else:
            raise NotImplementedError(f'BinaryExprPattern: {op} {lhs} {rhs}')
        

class IfPattern(RewritePattern):
    counter: int = 0

    @op_type_rewrite_pattern
    def match_and_rewrite(self, if_op: If, rewriter: PatternRewriter):
        cond = if_op.cond
        then_block = if_op.then.block
        else_block = if_op.orelse.block
        else_label = LabelOp(f"_if_else_{self.counter}")
        after_label = LabelOp(f"_if_after_{self.counter}")
        
        zero = LIOp(0)
        branch = BEQOp(cond, zero, f"_if_else_{self.counter}")

        rewriter.insert_op_after_matched_op(after_label)   
        rewriter.inline_block_after_matched_op(else_block)
        rewriter.insert_op_after_matched_op(else_label)   
        rewriter.insert_op_after_matched_op(JOp(f"_if_expr_after_{self.counter}"))
        rewriter.inline_block_after_matched_op(then_block)
        
        rewriter.replace_matched_op([zero, branch])
        self.counter += 1


class AndPattern(RewritePattern):
    counter: int = 0

    @op_type_rewrite_pattern
    def match_and_rewrite(self, and_op: EffectfulBinaryExpr, rewriter: PatternRewriter):
        if and_op.op.data != "and":
            return
        
        lhs_block = and_op.lhs.block
        lhs_: Yield = lhs_block._last_op.value
        rhs_block = and_op.rhs.block
        rhs_: Yield = rhs_block._last_op.value
        

        after_label = LabelOp(f"_and_after_{self.counter}")
        
        zero = LIOp(0)
        branch = BEQOp(lhs_, zero, f"_and_after_{self.counter}")

        res = AllocOp()
        store_lhs = SWOp(lhs_, res.rd, 0)
        store_rhs = SWOp(rhs_, res.rd, 0)
        load_res = LWOp(res, 0)
        
        rewriter.insert_op_after_matched_op(load_res)
        rewriter.insert_op_after_matched_op([store_rhs, after_label])
        rewriter.inline_block_after_matched_op(rhs_block)
        rewriter.insert_op_after_matched_op([store_lhs, branch])
        rewriter.inline_block_after_matched_op(lhs_block)
        rewriter.replace_matched_op([res, zero], [load_res.rd])
        
        self.counter += 1


class OrPattern(RewritePattern):
    counter: int = 0

    @op_type_rewrite_pattern
    def match_and_rewrite(self, or_op: EffectfulBinaryExpr, rewriter: PatternRewriter):
        if or_op.op.data != "or":
            return
        
        lhs_block = or_op.lhs.block
        lhs_: Yield = lhs_block._last_op.value
        rhs_block = or_op.rhs.block
        rhs_: Yield = rhs_block._last_op.value
        
        after_label = LabelOp(f"_or_after_{self.counter}")
        
        one = LIOp(1)
        branch = BEQOp(lhs_, one, f"_or_after_{self.counter}")
        
        res = AllocOp()
        store_lhs = SWOp(lhs_, res.rd, 0)
        store_rhs = SWOp(rhs_, res.rd, 0)
        load_res = LWOp(res, 0)
        
        rewriter.insert_op_after_matched_op(load_res)
        rewriter.insert_op_after_matched_op([store_rhs, after_label])
        rewriter.inline_block_after_matched_op(rhs_block)
        rewriter.insert_op_after_matched_op([store_lhs, branch])
        rewriter.inline_block_after_matched_op(lhs_block)
        rewriter.replace_matched_op([res, one], [load_res.rd])
        
        self.counter += 1


class IfExprPattern(RewritePattern):
    counter: int = 0

    @op_type_rewrite_pattern
    def match_and_rewrite(self, if_op: IfExpr, rewriter: PatternRewriter):
        
        cond = if_op.cond
        then_block = if_op.then.block
        else_block = if_op.or_else.block
        else_: Yield = else_block._last_op
        then_: Yield = then_block._last_op
        after_label = LabelOp(f"_if_expr_after_{self.counter}")
        else_label = LabelOp(f"_if_expr_else_{self.counter}")

        zero = LIOp(0)
        branch = BEQOp(cond, zero, f"_if_expr_else_{self.counter}")
        jump = JOp(f"_if_expr_after_{self.counter}")
        
        res = AllocOp()

        store_then = SWOp(then_.value, res.rd, 0)
        store_else = SWOp(else_.value, res.rd, 0)
        ret = LWOp(res.rd, 0)
        
        rewriter.insert_op_after_matched_op([store_else, after_label, ret])  
        rewriter.inline_block_after_matched_op(else_block)
        rewriter.insert_op_after_matched_op([store_then, jump, else_label])
        rewriter.inline_block_after_matched_op(then_block)
        # Need to yield the else_.value
        rewriter.replace_matched_op([zero, res, branch], [ret.rd])
        
        self.counter += 1


class WhilePattern(RewritePattern):
    counter: int = 0

    @op_type_rewrite_pattern
    def match_and_rewrite(self, while_op: While, rewriter: PatternRewriter):
        cond = while_op.cond.block
        body = while_op.body.block
        start_label = LabelOp(f"_while_start_{self.counter}")
        after_label = LabelOp(f"_while_after_{self.counter}")
        zero = LIOp(0)
        branch = BEQOp(cond._last_op.value, zero, f"_while_after_{self.counter}")

        rewriter.insert_op_after_matched_op(after_label)
        rewriter.insert_op_after_matched_op(JOp(f"_while_start_{self.counter}"))
        rewriter.inline_block_after_matched_op(body)   
        rewriter.insert_op_after_matched_op(branch)
        rewriter.inline_block_after_matched_op(cond)
        rewriter.replace_matched_op([zero, start_label])
        self.counter += 1


class ListExprPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, list_expr: ListExpr, rewriter: PatternRewriter):
        elems: list[SSAValue] = list_expr.elems
        # Constants
        size = LIOp(len(elems) * 4 + 4)
        length = LIOp(len(elems))
        
        # Malloc
        res = CallOp("_malloc", size)
        
        # List initialise
        s_len = SWOp(length, res.result, 0)
        ops = [size, length, res, s_len]
        for i in range(len(elems)):
            ops.append(SWOp(elems[i], res.result, 4*(i+1)))

        rewriter.replace_matched_op(ops, [res.result])


class GetAddressPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, get_address: GetAddress, rewriter: PatternRewriter):
        val = get_address.value
        index = get_address.index
        # Constants
        zero = LIOp(0)
        one = LIOp(1)
        four = LIOp(4)
        # Check List is not None
        maybe_fail_none = BEQOp(val, zero, f"_list_index_none")
        
        # Check Index is not out of bounds
        is_neg = SLTIOp(index, 0) # index < 0
        add_ = AddIOp(index, 1)
        length = LWOp(val, 0)
        is_big = SLTOp(length, add_) # index < length
        is_oob = OROp(is_neg, is_big) # index < 0 or index >= length
        maybe_fail_oob = BEQOp(is_oob, one, f"_list_index_oob")
        
        # Calculate Address
        mul = MULOp(add_, four)
        add = AddOp(val, mul)
        # Replace Op
        rewriter.replace_matched_op([zero, one, four, \
                                        maybe_fail_none, \
                                        add_, is_neg, length, is_big, is_oob, maybe_fail_oob,\
                                        mul, add])


class IndexStringPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, index_str: IndexString, rewriter: PatternRewriter):
        val = index_str.value
        index = index_str.index
        # Constants
        zero = LIOp(0)
        one = LIOp(1)
        four = LIOp(4)
        # Check List is not None
        maybe_fail_none = BEQOp(val, zero, f"_list_index_none")
        
        # Check Index is not out of bounds
        is_neg = SLTIOp(index, 0, comment="index < 0")
        add_ = AddIOp(index, 1)
        length = LWOp(val, 0)
        is_big = SLTOp(length, add_, comment="index < length")
        is_oob = OROp(is_neg, is_big, comment="index < 0 or index >= length")
        maybe_fail_oob = BEQOp(is_oob, one, f"_list_index_oob")
        
        # Calculate Address
        mul = MULOp(add_, four)
        add = AddOp(val, mul)
        char = LWOp(add, 0)
        
        # Constants
        size = LIOp(8)
        
        # Malloc
        res = CallOp("_malloc", size)
        
        # List initialise
        s_len = SWOp(one, res.result, 0)
        s_char = SWOp(char, res.result, 4)
        memloc = AllocOp()
        res_addr = SWOp(res.result, memloc, 0)
        
        # Replace Op
        rewriter.replace_matched_op([zero, one, four, \
                                        maybe_fail_none, \
                                        add_, is_neg, length, is_big, is_oob, maybe_fail_oob,\
                                        mul, add, char, size, res, s_len, s_char, memloc, res_addr], [memloc.rd])



class YieldPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, yield_: Yield, rewriter: PatternRewriter):
        rewriter.erase_matched_op()


class FuncDefPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, func: FuncDef, rewriter: PatternRewriter):
        new_func = FuncOp.create(
            result_types=[],
            properties={"func_name": StringAttr(func.func_name.data)},
        )
        new_region = rewriter.move_region_contents_to_new_regions(func.func_body)
        new_func.add_region(new_region)
        for arg in new_region.blocks[0].args:
            rewriter.modify_block_argument_type(arg, RegisterType())

        rewriter.replace_op(func, [new_func])


class ReturnPattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, ret: Return, rewriter: PatternRewriter):
        rewriter.replace_op(ret, [ReturnOp(ret.value)])


class ChocoFlatToRISCVSSA(ModulePass):
    name = "choco-flat-to-riscv-ssa"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    LiteralPattern(),
                    CallPattern(),
                    UnaryExprPattern(),
                    BinaryExprPattern(),
                    StorePattern(),
                    LoadPattern(),
                    AllocPattern(),
                    IfPattern(),
                    AndPattern(),
                    OrPattern(),
                    IfExprPattern(),
                    WhilePattern(),
                    ListExprPattern(),
                    GetAddressPattern(),
                    IndexStringPattern(),
                    FuncDefPattern(),
                    ReturnPattern(),
                ]
            ),
            apply_recursively=True,
        )

        walker.rewrite_module(op)

        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    YieldPattern(),
                ]
            ),
            apply_recursively=True,
        )

        walker.rewrite_module(op)
