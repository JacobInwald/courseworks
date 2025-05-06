# type: ignore

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import MLContext, Operation, SSAValue
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
)
from xdsl.printer import Printer

import riscv.dialect as riscv
import riscv.ssa_dialect as riscvssa
from choco.dialects.choco_flat import FuncDef
from riscv.dialect import Register, RegisterAttr


def allocate_registers(
    func: FuncDef,
) -> Tuple[int, Dict[SSAValue, int], int, Dict[Operation, int]]:
    """
    Allocate each infinite register to a place in the stack.
    returns the number of register spilled, and the position of
    each infinite register on the stack.
    """
    spilled_reg = 0
    stack_vars = 0
    stack_pos = dict()
    alloc_to_stack_var = dict()
    for arg in func.func_body.blocks[0].args:
        stack_pos[arg] = spilled_reg
        spilled_reg += 1
    for op in func.func_body.ops:
        for result in op.results:
            stack_pos[result] = spilled_reg
            spilled_reg += 1
        if isinstance(op, riscvssa.AllocOp):
            alloc_to_stack_var[op] = stack_vars
            stack_vars += 1
    return spilled_reg, stack_pos, stack_vars, alloc_to_stack_var


@dataclass(eq=False)
class RiscvToRiscvSSAPattern(RewritePattern):
    """
    Rewrite a single RISCV_SSA operation into a RISCV operation, given
    the allocation of registers.
    """

    ctx: MLContext
    func: FuncDef
    stack_pos: Dict[SSAValue, int]
    alloc_to_stack_var: Dict[SSAValue, int]
    """Position of the variables on the stack."""
    printer: Printer
    output: StringIO
    global_stack_pos: Optional[Dict[SSAValue, int]] = field(default=None)

    def add_stack_allocation(
        self, func: riscvssa.FuncOp, spilled_reg: int, stack_vars: int, is_main=False
    ):
        """
        Allocate data on the stack at the beginning of the
        module, and deallocate it at the end.
        """
        header_ops: List[Operation] = [
            riscv.AddIOp("sp", "sp", -4, "Reserve space for ra"),
            riscv.SWOp("ra", "sp", 0, "Store return address"),
            riscv.AddIOp(
                "sp",
                "sp",
                -4 * spilled_reg,
                "Reserve stack space for spilled registers",
            ),
        ]
        if stack_vars > 0:
            header_ops.append(
                riscv.AddIOp(
                    "sp",
                    "sp",
                    -4 * stack_vars,
                    "Reserve stack space for stack-allocated memory",
                )
            )
        if is_main:
            header_ops.append(
                riscv.MVOp("tp", "sp", "Move main stack pointer to special register")
            )

        idx = 0
        for arg in func.func_body.blocks[0].args:
            header_ops += self.store_variable_from_register(
                RegisterAttr.from_name(f"a{idx}"), arg
            )
            idx += 1

        footer_ops: List[Operation] = [
            riscv.CommentOp(""),
            riscv.CommentOp("Footer Ops"),
            riscv.LabelOp("_" + func.properties["func_name"].data + "_return"),
            riscv.AddIOp(
                "sp",
                "sp",
                4 * spilled_reg,
                "Free stack space reserved for spilled registers",
            ),
        ]
        if stack_vars:
            footer_ops.append(
                riscv.AddIOp(
                    "sp",
                    "sp",
                    4 * stack_vars,
                    "Free stack space reserved for stack-allocated memory",
                )
            )
        footer_ops += [
            riscv.LWOp("ra", "sp", 0, "Store return address"),
            riscv.AddIOp("sp", "sp", 4, "Free space for ra"),
        ]
        block = func.regions[0].blocks[0]
        if block.first_op:
            block.insert_ops_before(header_ops, block.first_op)
        else:
            block.add_ops(header_ops)
        if block.last_op:
            block.insert_ops_after(footer_ops, block.last_op)
        else:
            block.add_ops(footer_ops)

    def get_variable_on_register(self, val: SSAValue, reg: Register) -> List[Operation]:
        """Place a variable on a specific register."""

        # Get the variable name
        full = self.output.getvalue()
        self.printer.print_operand(val)
        formatted_op = self.output.getvalue()
        formatted_op = formatted_op[len(full) :]

        # Get its address if the variable is defined in main
        if val not in self.stack_pos:
            if self.global_stack_pos is None or val not in self.global_stack_pos:
                raise Exception("Critical error in riscv variable allocator.")
            pos = self.global_stack_pos[val]
            if pos * 4 > 2**12:
                raise NotImplementedError(
                    "Register allocator is not working for more than 128 variables."
                )
            op = riscv.LWOp(reg, "tp", pos * 4, f"Unspill register '{formatted_op}'")
            return [op]

        pos = self.stack_pos[val]
        if pos * 4 > 2**12:
            raise NotImplementedError(
                "Register allocator is not working for more than 128 variables."
            )

        op = riscv.LWOp(reg, "sp", pos * 4, f"Unspill register '{formatted_op}'")
        return [op]

    def store_variable_from_register(
        self, reg: Register, val: SSAValue
    ) -> List[Operation]:
        """
        Store a variable into its place in the stack, knowing the
        current position of the variable in the registers.
        """
        pos = self.stack_pos[val]
        if pos * 4 > 2**12:
            raise NotImplementedError(
                "Register allocator is not working for more than 128 variables."
            )
        op = riscv.SWOp(reg, "sp", pos * 4, "Spill register")
        return [op]

    def rewrite_ecall(self, op: riscvssa.ECALLOp, rewriter: PatternRewriter) -> None:
        new_ops = []
        new_ops.extend(
            self.get_variable_on_register(op.syscall_num, RegisterAttr.from_name("a7"))
        )
        for idx, operand in enumerate(op.args):
            new_ops.extend(
                self.get_variable_on_register(
                    operand, RegisterAttr.from_name("a" + str(idx))
                )
            )
        new_ops.append(riscv.ECALLOp())
        rewriter.replace_op(op, new_ops, [None] * len(op.results), safe_erase=True)

    def rewrite_call(self, op: riscvssa.CallOp, rewriter: PatternRewriter) -> None:
        new_ops = [riscv.CommentOp(""), riscv.CommentOp(f"{op.name}")]
        for idx, operand in enumerate(op.args):
            new_ops.extend(
                self.get_variable_on_register(
                    operand, RegisterAttr.from_name("a" + str(idx))
                )
            )
        jump = riscv.JALOp(RegisterAttr.from_name("ra"), op.func_name.data)
        new_ops = new_ops + [jump]

        assert len(op.results) in [
            0,
            1,
        ], "Only functions with zero or one return value supported"

        if len(op.results) == 1:
            new_ops.extend(
                self.store_variable_from_register(
                    RegisterAttr.from_name("a0"), op.results[0]
                )
            )
        rewriter.replace_op(op, new_ops, [None] * len(op.results), safe_erase=True)

    def rewrite_alloc(self, op: riscvssa.AllocOp, rewriter: PatternRewriter) -> None:
        stack_pos = 4 * (self.alloc_to_stack_var[op] + len(self.stack_pos))
        new_ops = [
            riscv.AddIOp(
                RegisterAttr.from_name("t0"),
                RegisterAttr.from_name("sp"),
                stack_pos,
                "Save ptr of stack-slot into register",
            )
        ]
        new_ops.extend(
            self.store_variable_from_register(
                RegisterAttr.from_name("t0"), op.results[0]
            )
        )
        rewriter.replace_op(op, new_ops, [None] * len(op.results), safe_erase=True)

    def rewrite_return(self, ret: riscvssa.ReturnOp, rewriter: PatternRewriter):
        new_ops = self.get_variable_on_register(ret.value, RegisterAttr.from_name("a0"))
        new_ops.append(
            riscv.JOp("_" + ret.parent_op().properties["func_name"].data + "_return")
        )
        rewriter.replace_op(ret, new_ops)

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter):
        if op.parent_op() is not self.func:
            return

        if isinstance(op, riscvssa.ECALLOp):
            self.rewrite_ecall(op, rewriter)
            return
        if isinstance(op, riscvssa.CallOp):
            self.rewrite_call(op, rewriter)
            return
        if isinstance(op, riscvssa.AllocOp):
            self.rewrite_alloc(op, rewriter)
            return
        if isinstance(op, riscvssa.FuncOp):
            return
        if isinstance(op, riscvssa.ReturnOp):
            self.rewrite_return(op, rewriter)
            return

        # Get the matching operation in RISCV
        name = op.name.split(".", maxsplit=1)
        if len(name) == 1:
            return None
        dialect, opname = name
        if dialect != "riscv_ssa":
            return None
        new_op_type = self.ctx.get_op("riscv." + opname)

        full = self.output.getvalue()
        self.printer.print_op(op)
        formatted_op = self.output.getvalue()
        formatted_op = formatted_op[len(full) : -1]

        # The operations that will be added
        new_ops = [riscv.CommentOp(""), riscv.CommentOp(f"{formatted_op}")]

        # The properties of the riscv operation that will be created
        new_op_properties = op.properties.copy()
        assert len(op.operands) <= 2
        assert len(op.results) <= 1

        # Fill the properties with the right values for operands and results.
        # Also move operand variables to specific registers.
        if len(op.operands) > 0:
            new_ops.extend(
                self.get_variable_on_register(
                    op.operands[0], RegisterAttr.from_name("t1")
                )
            )
            new_op_properties["rs1"] = RegisterAttr.from_name("t1")

        if len(op.operands) > 1:
            new_ops.extend(
                self.get_variable_on_register(
                    op.operands[1], RegisterAttr.from_name("t2")
                )
            )
            new_op_properties["rs2"] = RegisterAttr.from_name("t2")

        if len(op.results) != 0:
            new_op_properties["rd"] = RegisterAttr.from_name("t0")

        # Create the new corresponding operation
        new_ops.append(new_op_type.create(properties=new_op_properties))

        # Place the result in its right place on the stack
        if len(op.results) != 0:
            new_ops.extend(
                self.store_variable_from_register(
                    RegisterAttr.from_name("t0"), op.results[0]
                )
            )

        rewriter.replace_op(op, new_ops, [None] * len(op.results), safe_erase=True)


def add_print(mod: ModuleOp):
    new_ops = [
        riscv.LabelOp("_print_int"),
        riscv.AddIOp("sp", "sp", -12),
        riscv.MVOp("t1", "a0"),
        riscv.LIOp("t2", 10),
        riscv.SLTIOp("t6", "t1", 0),
        riscv.SLTIOp("t6", "t1", 0),
        riscv.LIOp("t5", 2),
        riscv.MULOp("t6", "t5", "t6"),
        riscv.LIOp("t5", 1),
        riscv.SubOp("t5", "t5", "t6"),
        riscv.MULOp("t1", "t5", "t1"),
        riscv.MVOp("t6", "zero"),
    ]

    for idx in range(10, 1, -1):
        new_ops += [
            riscv.REMOp("t0", "t1", "t2"),
            riscv.AddIOp("t0", "t0", 48),
            riscv.SLTIOp("t3", "t1", 1),
            riscv.AddOp("t6", "t6", "t3"),
            riscv.SBOp("t0", "sp", idx),
            riscv.DIVOp("t1", "t1", "t2"),
        ]

    new_ops += [
        riscv.REMOp("t0", "t1", "t2"),
        riscv.AddIOp("t0", "t0", 48),
        riscv.SLTIOp("t3", "t1", 1),
        riscv.SLTOp("t4", "zero", "a0"),
        riscv.SLTOp("t5", "a0", "zero"),
        riscv.OROp("t4", "t4", "t5"),
        riscv.ANDOp("t3", "t3", "t4"),
        riscv.AddOp("t6", "t6", "t3"),
        riscv.SBOp("t0", "sp", 1),
        riscv.DIVOp("t1", "t1", "t2"),
    ]

    new_ops += [
        riscv.SLTIOp("t5", "t5", -1),
        riscv.AddOp("t6", "t6", "t5"),
        riscv.LIOp("t5", 45),
        riscv.AddOp("t4", "sp", "t6"),
        riscv.SBOp("t5", "t4", 0),
        riscv.LIOp("t4", -1),
        riscv.SLTOp("t3", "t4", "a0"),
        riscv.AddOp("t6", "t6", "t3"),
    ]

    new_ops += [
        riscv.LIOp("t0", 10),
        riscv.SBOp("t0", "sp", 11),
        riscv.LIOp("a0", 1),
        riscv.MVOp("a1", "sp"),
        riscv.AddOp("a1", "a1", "t6"),
        riscv.LIOp("a2", 12),
        riscv.SubOp("a2", "a2", "t6"),
        riscv.LIOp("a7", 64),
        riscv.ECALLOp(),
        riscv.AddIOp("sp", "sp", 12),
        riscv.RETOp(),
    ]

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def add_input(mod: ModuleOp):
    new_ops = [
        riscv.LabelOp("_input"),
        riscv.AddIOp("sp", "sp", -1024),
        riscv.SWOp("ra", "sp", 1020),
        riscv.LIOp("a0", 0),
        riscv.MVOp("a1", "sp"),
        riscv.LIOp("a2", 1020),
        riscv.LIOp("a7", 63),
        riscv.ECALLOp(),
        riscv.LIOp("t1", 4),
        riscv.MVOp("t4", "a0"),
        riscv.AddIOp("t4", "t4", -1),
        riscv.MULOp("a0", "a0", "t1"),
        riscv.AddOp("a0", "a0", "t1"),
        riscv.JALOp("ra", "_malloc", "Allocate memory for new list"),
        riscv.LIOp("t1", 4),
        riscv.SWOp("t4", "a0", 0),
        riscv.LIOp("t5", 0),
        riscv.BEQOp("t4", "t5", "_input_loop_finished"),
        riscv.LabelOp("_input_loop_header"),
        riscv.AddOp("t3", "sp", "t5"),
        riscv.LBOp("t6", "t3", 0),
        riscv.MULOp("t3", "t5", "t1"),
        riscv.AddOp("t3", "a0", "t3"),
        riscv.SWOp("t6", "t3", 4),
        riscv.AddIOp("t5", "t5", 1),
        riscv.BNEOp("t4", "t5", "_input_loop_header"),
        riscv.LabelOp("_input_loop_finished"),
        riscv.LWOp("ra", "sp", 1020),
        riscv.AddIOp("sp", "sp", 1024),
        riscv.RETOp(),
    ]

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def string_on_stack_ops(message: str) -> Tuple[int, List[Operation]]:
    # We align the stack to 4 bytes
    num_stack_space = len(message) + (4 - len(message)) % 4
    ops = [riscv.AddIOp("sp", "sp", -num_stack_space)]
    for idx, char in enumerate(message):
        ops.append(riscv.LIOp("t0", ord(char)))
        ops.append(riscv.SBOp("t0", "sp", idx))
    return num_stack_space, ops


def print_message_ops(message: str) -> List[Operation]:
    string_size, string_ops = string_on_stack_ops(message)
    new_ops = string_ops + [
        riscv.LIOp("a0", 1),  # stdout stream
        riscv.MVOp("a1", "sp"),  # string pointer
        riscv.LIOp("a2", len(message)),  # string size
        riscv.LIOp("a7", 64),  # print string code
        riscv.ECALLOp(),
        riscv.AddIOp("sp", "sp", string_size),
    ]
    return new_ops


def add_print_bool(mod: ModuleOp):
    string_size, string_ops = string_on_stack_ops("False\n\0True\n\0")
    new_ops = (
        [
            riscv.LabelOp("_print_bool"),
        ]
        + string_ops
        + [
            riscv.LIOp("t1", 7),
            riscv.SLTUOp("t2", "zero", "a0"),
            riscv.MULOp("t1", "t1", "t2"),
            riscv.AddOp("t1", "t1", "sp"),
            riscv.LIOp("t3", 6),
            riscv.SLTUOp("t4", "zero", "a0"),
            riscv.SubOp("t4", "t3", "t4"),
            riscv.LIOp("a0", 1),
            riscv.MVOp("a1", "t1"),
            riscv.MVOp("a2", "t4"),
            riscv.LIOp("a7", 64),
            riscv.ECALLOp(),
            riscv.AddIOp("sp", "sp", string_size),
            riscv.RETOp(),
        ]
    )

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def add_print_string(mod: ModuleOp):
    new_ops = [
        riscv.LabelOp("_print_str"),
        riscv.AddIOp("t0", "a0", 0, "Get address of string object"),
        riscv.LWOp("t2", "t0", 0, "Load length of string"),
        riscv.LIOp("t1", 0, "Set loop counter to zero"),
        riscv.SubOp(
            "sp", "sp", "t2", "Expand stack pointer by number of string elements"
        ),
        riscv.AddIOp("sp", "sp", -1, "Expand stack pointer for newline"),
        riscv.BEQOp("t1", "t2", "_print_str_loop_finished"),
        riscv.LabelOp("_print_str_loop_header"),
        riscv.LIOp("t6", 4, "Number of bytes per element"),
        riscv.MULOp("t3", "t1", "t6", "Distance from pointer in bytes"),
        riscv.AddOp("t4", "t0", "t3", "The address of the element in the string"),
        riscv.LWOp("t5", "t4", 4),
        riscv.AddOp("t4", "sp", "t1", "The address of the element on the stack"),
        riscv.SBOp("t5", "t4", 0, "Store character on stack"),
        riscv.AddIOp("t1", "t1", 1, "Increment loop counter"),
        riscv.BNEOp("t1", "t2", "_print_str_loop_header", "Continue loop"),
        riscv.LabelOp("_print_str_loop_finished"),
        riscv.AddOp("t4", "sp", "t1", "The address of the element on the stack"),
        riscv.LIOp("t5", ord("\n"), "Store newline character in output string"),
        riscv.SBOp("t5", "t4", 0, "Store character on stack"),
        riscv.LIOp("a0", 1, "Print to stdout"),
        riscv.MVOp(
            "a1", "sp", "syscall argument: the start address is the stack pointer"
        ),
        riscv.AddIOp("t3", "t2", 1, "Make room for newline"),
        riscv.MVOp("a2", "t3", "syscall argument: length of the string"),
        riscv.LIOp("a7", 64, "Request the print system call"),
        riscv.ECALLOp("Trigger the system call"),
        riscv.AddIOp("sp", "sp", 1, "Free the stack for newline"),
        riscv.AddOp("sp", "sp", "t2", "Free the stack"),
        riscv.RETOp(),
    ]

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def add_print_error(mod: ModuleOp, func_name: str, message: str):
    new_ops = [riscv.LabelOp(func_name)] + print_message_ops(message) + exit_ops(1)
    mod.regions[0].blocks[0].add_ops(new_ops)


def add_list_concat(mod: ModuleOp):
    new_ops = [
        riscv.LabelOp("_list_concat"),
        riscv.AddIOp("sp", "sp", -24, "Reserve stack space"),
        riscv.LWOp("t0", "a0", 0, "Load length of list a"),
        riscv.LWOp("t1", "a1", 0, "Load length of list b"),
        riscv.AddOp("t2", "t0", "t1", "Compute length of overall list"),
        riscv.LIOp("t3", 4, "Load size of a word in bytes"),
        riscv.MULOp("t4", "t2", "t3", "Compute amount of storage for list elements"),
        riscv.AddIOp("t4", "t4", 4, "Also consider space needed to store list size"),
        riscv.SWOp("ra", "sp", 0, "Save return address"),
        riscv.SWOp("t0", "sp", 4, "Save length of list a"),
        riscv.SWOp("t1", "sp", 8, "Save length of list b"),
        riscv.SWOp("t2", "sp", 12, "Save length of new list"),
        riscv.SWOp("a0", "sp", 16, "Save base ptr of list a"),
        riscv.SWOp("a1", "sp", 20, "Save base ptr of list b"),
        riscv.AddIOp("a0", "t4", 0),
        riscv.JALOp("ra", "_malloc", "Allocate memory for new list"),
        riscv.LWOp("ra", "sp", 0, "Restore return address"),
        riscv.LWOp("t0", "sp", 4, "Restore length of list a"),
        riscv.LWOp("t1", "sp", 8, "Restore length of list b"),
        riscv.LWOp("t2", "sp", 12, "Restore length of new list"),
        riscv.LWOp("t3", "sp", 16, "Restore base ptr of list a"),
        riscv.LWOp("t4", "sp", 20, "Restore base ptr of list b"),
        riscv.SWOp("t2", "a0", 0, "Store length of new list in list"),
        riscv.LIOp("t5", 0, "Set loop counter"),
        riscv.AddIOp("t6", "a0", 0),
        riscv.BEQOp("t0", "zero", "_list_concat_repeat_first_end"),
        riscv.LabelOp("_list_concat_repeat_first"),
        riscv.AddIOp("t5", "t5", 1),
        riscv.AddIOp("t3", "t3", 4),
        riscv.AddIOp("t6", "t6", 4),
        riscv.LWOp("t2", "t3", 0, "Load list element from a"),
        riscv.SWOp("t2", "t6", 0, "Store list element in new list"),
        riscv.BNEOp("t5", "t0", "_list_concat_repeat_first"),
        riscv.LabelOp("_list_concat_repeat_first_end"),
        riscv.LIOp("t5", 0, "Set loop counter"),
        riscv.BEQOp("t1", "zero", "_list_concat_repeat_second_end"),
        riscv.LabelOp("_list_concat_repeat_second"),
        riscv.AddIOp("t5", "t5", 1),
        riscv.AddIOp("t4", "t4", 4),
        riscv.AddIOp("t6", "t6", 4),
        riscv.LWOp("t2", "t4", 0, "Load list element from a"),
        riscv.SWOp("t2", "t6", 0, "Store list element in new list"),
        riscv.BNEOp("t5", "t1", "_list_concat_repeat_second"),
        riscv.LabelOp("_list_concat_repeat_second_end"),
        riscv.AddIOp("sp", "sp", 24, "Free stack space"),
        riscv.RETOp(),
    ]

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def add_str_eq(mod: ModuleOp):
    new_ops = [
        riscv.LabelOp("_str_eq"),
        riscv.LWOp("t0", "a0", 0, "Load length of first string"),
        riscv.LWOp("t1", "a1", 0, "Load length of second string"),
        riscv.BNEOp(
            "t0", "t1", "_str_eq_return_false", "return false if length are not equal"
        ),
        riscv.BEQOp(
            "t0",
            "zero",
            "_str_eq_return_true",
            "return true if both length are equal to 0",
        ),
        riscv.AddIOp("t2", "a0", 4, "First string index iterator"),
        riscv.AddIOp("t3", "a1", 4, "Second string index iterator"),
        riscv.LIOp("t5", 4, "Size of an integer"),
        riscv.MULOp("t5", "t0", "t5", "Size of the strings in bytes"),
        riscv.AddOp("t4", "a0", "t5", "First string iterator last element"),
        riscv.AddIOp("t4", "t4", 4, "First string end iterator"),
        riscv.LabelOp("_str_eq_loop_begin"),
        riscv.LWOp("t5", "t2", 0, "Get the first string character"),
        riscv.LWOp("t6", "t3", 0, "Get the first string character"),
        riscv.BNEOp(
            "t5",
            "t6",
            "_str_eq_return_false",
            "If the characters are different, return false",
        ),
        riscv.AddIOp("t2", "t2", 4),
        riscv.AddIOp("t3", "t3", 4),
        riscv.BLTOp(
            "t2",
            "t4",
            "_str_eq_loop_begin",
            "If we are not at the end of the string, continue",
        ),
        riscv.LabelOp("_str_eq_return_true"),
        riscv.LIOp("a0", 1),
        riscv.RETOp(),
        riscv.LabelOp("_str_eq_return_false"),
        riscv.LIOp("a0", 0),
        riscv.RETOp(),
    ]

    mod.regions[0].blocks[0].add_ops(new_ops)
    return mod


def exit_ops(exit_code: int) -> List[Operation]:
    return [
        riscv.CommentOp(""),
        riscv.CommentOp("Exit program"),
        riscv.LIOp("a0", exit_code),
        riscv.LIOp("a7", 93),
        riscv.ECALLOp(),
    ]


def add_exit(mod: ModuleOp):
    mod.regions[0].blocks[0].add_ops(exit_ops(0))


def add_return(op: Operation):
    new_ops = [riscv.RETOp()]

    op.regions[0].blocks[0].add_ops(new_ops)


class RISCVSSAToRISCV(ModulePass):
    name = "riscv-ssa-to-riscv"

    def apply(self, ctx: MLContext, mod: ModuleOp) -> None:
        """
        Translate a riscvssa program into an equivalent RISCV program.
        """

        output = StringIO()
        printer = Printer(
            output,
        )
        printer.print_op(mod)

        assert len(mod.ops) == 1, "expected at least one main function"
        main = mod.ops.first

        (
            global_spilled_reg,
            global_stack_pos,
            global_stack_vars,
            global_alloc_to_stack_var,
        ) = allocate_registers(main)

        # Allocate registers in all function definitions
        for func in main.func_body.ops:
            if not isinstance(func, riscvssa.FuncOp):
                continue
            spilled_reg, stack_pos, stack_vars, alloc_to_stack_var = allocate_registers(
                func
            )
            pattern = RiscvToRiscvSSAPattern(
                ctx,
                func,
                stack_pos,
                alloc_to_stack_var,
                printer,
                output,
                global_stack_pos=global_stack_pos,
            )
            pattern.add_stack_allocation(func, spilled_reg, stack_vars)
            add_return(func)
            walker = PatternRewriteWalker(
                GreedyRewritePatternApplier([pattern]),
                apply_recursively=True,
                walk_reverse=True,
            )
            walker.rewrite_module(func)

        # Allocate registers in the main function
        pattern = RiscvToRiscvSSAPattern(
            ctx, main, global_stack_pos, global_alloc_to_stack_var, printer, output
        )
        pattern.add_stack_allocation(
            main, global_spilled_reg, global_stack_vars, is_main=True
        )
        walker = PatternRewriteWalker(
            GreedyRewritePatternApplier([pattern]),
            apply_recursively=True,
            walk_reverse=True,
        )
        walker.rewrite_module(main)
        add_exit(main)

        add_print(mod)
        add_print_bool(mod)
        add_print_string(mod)
        add_input(mod)
        add_list_concat(mod)
        add_str_eq(mod)
        add_print_error(
            mod, "_error_len_none", "TypeError: object of type 'NoneType' has no len()"
        )
        add_print_error(mod, "_list_index_oob", "IndexError: list index out of range")
        add_print_error(
            mod, "_list_index_none", "TypeError: 'NoneType' object is not subscriptable"
        )
        add_print_error(mod, "_error_div_zero", "DivByZero: Division by zero")
        i = 0
        for func in list(main.func_body.ops):
            if not isinstance(func, riscvssa.FuncOp):
                continue
            func.detach()
            main.func_body.blocks[0].add_op(func)
