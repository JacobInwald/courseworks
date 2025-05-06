from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union

from xdsl.dialects.builtin import AnyIntegerAttr, IntegerAttr, StringAttr
from xdsl.ir import (
    Attribute,
    Dialect,
    Operation,
    OpResult,
    ParametrizedAttribute,
    SSAValue,
    TypeAttribute,
)
from xdsl.irdl import (
    IRDLOperation,
    Operand,
    OptOperand,
    OptOpResult,
    Region,
    VarOperand,
    irdl_attr_definition,
    irdl_op_definition,
    operand_def,
    opt_operand_def,
    opt_prop_def,
    opt_result_def,
    prop_def,
    region_def,
    result_def,
    var_operand_def,
)
from xdsl.traits import (
    NoTerminator,
)

import riscv.dialect


@irdl_attr_definition
class RegisterType(ParametrizedAttribute, TypeAttribute):
    name = "riscv_ssa.reg"


class Riscv1Rd1Rs1ImmOperation(IRDLOperation):
    rd: OpResult = result_def(RegisterType)
    rs1: Operand = operand_def(RegisterType)
    immediate: AnyIntegerAttr = prop_def(AnyIntegerAttr)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs1: Union[Operation, SSAValue],
        immediate: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(immediate, int):
            immediate = IntegerAttr.from_int_and_width(immediate, 32)

        properties: Dict[str, Any] = {
            "immediate": immediate,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(
            operands=[rs1], result_types=[RegisterType()], properties=properties
        )


class Riscv2Rs1ImmOperation(IRDLOperation):
    rs1: Operand = operand_def(RegisterType)
    rs2: Operand = operand_def(RegisterType)
    immediate: AnyIntegerAttr = prop_def(AnyIntegerAttr)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs1: Union[Operation, SSAValue],
        rs2: Union[Operation, SSAValue],
        immediate: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(immediate, int):
            immediate = IntegerAttr.from_int_and_width(immediate, 32)

        properties: Dict[str, Any] = {
            "immediate": immediate,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(operands=[rs1, rs2], properties=properties)


class Riscv2Rs1OffOperation(IRDLOperation):
    rs1: Operand = operand_def(RegisterType)
    rs2: Operand = operand_def(RegisterType)
    offset: AnyIntegerAttr | riscv.dialect.LabelAttr = prop_def(
        AnyIntegerAttr | riscv.dialect.LabelAttr
    )
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs1: Union[Operation, SSAValue],
        rs2: Union[Operation, SSAValue],
        offset: Union[int, AnyIntegerAttr, riscv.dialect.LabelAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(offset, int):
            offset = IntegerAttr.from_int_and_width(offset, 32)
        if isinstance(offset, str):
            offset = riscv.dialect.LabelAttr.from_str(offset)

        properties: Dict[str, Any] = {
            "offset": offset,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(operands=[rs1, rs2], properties=properties)


class Riscv1Rd2RsOperation(IRDLOperation):
    rd: OpResult = result_def(RegisterType)
    rs1: Operand = operand_def(RegisterType)
    rs2: Operand = operand_def(RegisterType)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs1: Union[Operation, SSAValue],
        rs2: Union[Operation, SSAValue],
        comment: Optional[str] = None,
    ):
        properties: Dict[str, Any] = {}
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(
            operands=[rs1, rs2], properties=properties, result_types=[RegisterType()]
        )


class Riscv1Rs1Rt1OffOperation(IRDLOperation):
    rs: OpResult = result_def(RegisterType)
    rt: Operand = operand_def(RegisterType)
    offset: AnyIntegerAttr = prop_def(AnyIntegerAttr)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rt: Union[Operation, SSAValue],
        offset: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(offset, int):
            offset = IntegerAttr.from_int_and_width(offset, 32)

        properties: Dict[str, Any] = {
            "offset": offset,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(operands=[rt], properties=properties)


class Riscv1OffOperation(IRDLOperation):
    offset: AnyIntegerAttr | riscv.dialect.LabelAttr = prop_def(
        AnyIntegerAttr | riscv.dialect.LabelAttr
    )
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        offset: Union[int, AnyIntegerAttr, riscv.dialect.LabelAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(offset, int):
            offset = IntegerAttr.from_int_and_width(offset, 32)
        if isinstance(offset, str):
            offset = riscv.dialect.LabelAttr.from_str(offset)

        properties: Dict[str, Any] = {
            "offset": offset,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(properties=properties)


class Riscv1Rd1ImmOperation(IRDLOperation):
    rd: OpResult = result_def(RegisterType)
    immediate: AnyIntegerAttr | riscv.dialect.LabelAttr = prop_def(
        AnyIntegerAttr | riscv.dialect.LabelAttr
    )
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        immediate: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(immediate, int):
            immediate = IntegerAttr.from_int_and_width(immediate, 32)

        properties: Dict[str, Any] = {
            "immediate": immediate,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(result_types=[RegisterType()], properties=properties)


class Riscv1Rd1OffOperation(IRDLOperation):
    rd: OpResult = result_def(RegisterType)
    offset: AnyIntegerAttr = prop_def(AnyIntegerAttr)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        offset: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(offset, int):
            offset = IntegerAttr.from_int_and_width(offset, 32)

        properties: Dict[str, Any] = {
            "offset": offset,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(properties=properties, result_types=[RegisterType()])


class Riscv1Rs1OffOperation(IRDLOperation):
    rs: Operand = operand_def(RegisterType)
    offset: AnyIntegerAttr = prop_def(AnyIntegerAttr)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs: Union[Operation, SSAValue],
        offset: Union[int, AnyIntegerAttr],
        comment: Optional[str] = None,
    ):
        if isinstance(offset, int):
            offset = IntegerAttr.from_int_and_width(offset, 32)

        properties: Dict[str, Any] = {
            "offset": offset,
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(operands=[rs], properties=properties)


class Riscv1Rd1RsOperation(IRDLOperation):
    rd: OpResult = result_def(RegisterType)
    rs: Operand = operand_def(RegisterType)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        rs: Union[Operation, SSAValue],
        comment: Optional[str] = None,
    ):
        properties: Dict[str, Any] = {}
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(
            operands=[rs], result_types=[RegisterType()], properties=properties
        )


class RiscvNoParamsOperation(IRDLOperation):
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(self, comment: Optional[str] = None):
        properties: Dict[str, Any] = {}
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(properties=properties)


@irdl_op_definition
class LBOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.lb"


@irdl_op_definition
class LBUOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.lbu"


@irdl_op_definition
class LHOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.lh"


@irdl_op_definition
class LHUOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.lhu"


@irdl_op_definition
class LWOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.lw"


# Stores


@irdl_op_definition
class SBOp(Riscv2Rs1ImmOperation):
    name = "riscv_ssa.sb"


@irdl_op_definition
class SHOp(Riscv2Rs1ImmOperation):
    name = "riscv_ssa.sh"


@irdl_op_definition
class SWOp(Riscv2Rs1ImmOperation):
    name = "riscv_ssa.sw"


# Branches


@irdl_op_definition
class BEQOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.beq"


@irdl_op_definition
class BNEOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.bne"


@irdl_op_definition
class BLTOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.blt"


@irdl_op_definition
class BGEOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.bge"


@irdl_op_definition
class BLTUOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.bltu"


@irdl_op_definition
class BGEUOp(Riscv2Rs1OffOperation):
    name = "riscv_ssa.bgeu"


# Shifts


@irdl_op_definition
class SLLOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.sll"


@irdl_op_definition
class SLLIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.slli"


@irdl_op_definition
class SRLOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.srl"


@irdl_op_definition
class SRLIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.srli"


@irdl_op_definition
class SRAOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.sra"


@irdl_op_definition
class SRAIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.srai"


# Arithmetic


@irdl_op_definition
class AddOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.add"


@irdl_op_definition
class AddIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.addi"


@irdl_op_definition
class SubOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.sub"


@irdl_op_definition
class LUIOp(Riscv1Rd1ImmOperation):
    name = "riscv_ssa.lui"


@irdl_op_definition
class LIOp(Riscv1Rd1ImmOperation):
    name = "riscv_ssa.li"


@irdl_op_definition
class AUIPCOp(Riscv1Rd1ImmOperation):
    name = "riscv_ssa.auipc"


# Logical


@irdl_op_definition
class XOROp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.xor"


@irdl_op_definition
class XORIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.xori"


@irdl_op_definition
class OROp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.or"


@irdl_op_definition
class ORIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.ori"


@irdl_op_definition
class ANDOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.and"


@irdl_op_definition
class ANDIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.andi"


# Compare


@irdl_op_definition
class SLTOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.slt"


@irdl_op_definition
class SLTIOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.slti"


@irdl_op_definition
class SLTUOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.sltu"


@irdl_op_definition
class SLTIUOp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.sltiu"


# Jump & Link


@irdl_op_definition
class JOp(Riscv1OffOperation):
    name = "riscv_ssa.j"


@irdl_op_definition
class JALOp(Riscv1Rd1ImmOperation):
    name = "riscv_ssa.jal"


@irdl_op_definition
class JALROp(Riscv1Rd1Rs1ImmOperation):
    name = "riscv_ssa.jalr"


# System


@irdl_op_definition
class ECALLOp(IRDLOperation):
    name = "riscv_ssa.ecall"
    syscall_num: Operand = operand_def(RegisterType)
    args: VarOperand = var_operand_def(RegisterType)


@irdl_op_definition
class EBREAKOp(IRDLOperation):
    name = "riscv_ssa.ebreak"


#  Optional Multiply-Divide Instruction Extension (RVM)


@irdl_op_definition
class MULOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.mul"


@irdl_op_definition
class MULHOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.mulh"


@irdl_op_definition
class MULHSUOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.mulhsu"


@irdl_op_definition
class MULHUOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.mulhu"


@irdl_op_definition
class DIVOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.div"


@irdl_op_definition
class DIVUOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.divu"


@irdl_op_definition
class REMOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.rem"


@irdl_op_definition
class REMUOp(Riscv1Rd2RsOperation):
    name = "riscv_ssa.remu"


@irdl_op_definition
class CallOp(IRDLOperation):
    name = "riscv_ssa.call"
    args: VarOperand = var_operand_def(RegisterType)
    func_name: StringAttr = prop_def(StringAttr)
    result: OptOpResult = opt_result_def(RegisterType)
    comment: StringAttr | None = opt_prop_def(StringAttr)

    def __init__(
        self,
        func_name: Union[str, StringAttr],
        args: List[Union[Operation, SSAValue]],
        has_result: bool = True,
        comment: Optional[Union[str, StringAttr]] = None,
    ):
        if isinstance(func_name, str):
            func_name = StringAttr(func_name)
        properties: Dict[str, Any] = {"func_name": func_name}
        if comment is not None:
            if isinstance(comment, str):
                comment = StringAttr(comment)
            properties["comment"] = comment
        super().__init__(
            operands=[args],
            result_types=[[RegisterType()]] if has_result else [[]],
            properties=properties,
        )


@irdl_op_definition
class LabelOp(IRDLOperation):
    name = "riscv_ssa.label"
    label: riscv.dialect.LabelAttr = prop_def(riscv.dialect.LabelAttr)

    def __init__(
        self,
        label: str,
        comment: Optional[str] = None,
    ):
        properties: Dict[str, Any] = {
            "label": riscv.dialect.LabelAttr.from_str(label),
        }
        if comment:
            properties["comment"] = StringAttr(comment)
        super().__init__(operands=[], result_types=[], properties=properties)


@irdl_op_definition
class DirectiveOp(IRDLOperation):
    name = "riscv_ssa.directive"
    directive: StringAttr = prop_def(StringAttr)
    value: StringAttr = prop_def(StringAttr)


@irdl_op_definition
class AllocOp(IRDLOperation):
    name = "riscv_ssa.alloc"
    rd: OpResult = result_def(RegisterType)

    def __init__(self):
        super().__init__(result_types=[RegisterType()])


@irdl_op_definition
class FuncOp(IRDLOperation):
    name = "riscv_ssa.func"

    func_name: StringAttr = prop_def(StringAttr)
    func_body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class ReturnOp(IRDLOperation):
    name = "riscv_ssa.return"
    value: OptOperand = opt_operand_def(RegisterType)

    def __init__(self, value: Optional[Union[Operation, SSAValue]] = None):
        operands: List[Operation | SSAValue] = []

        if value != None:
            operands.append(value)

        super().__init__(operands=operands)


riscv_ssa_attrs: List[Type[Attribute]] = [RegisterType]
riscv_ssa_ops: List[Type[Operation]] = [
    LBOp,
    LBUOp,
    LHOp,
    LHUOp,
    LWOp,
    SBOp,
    SHOp,
    SWOp,
    BEQOp,
    BNEOp,
    BLTOp,
    BGEOp,
    BLTUOp,
    BGEUOp,
    AddOp,
    AddIOp,
    SubOp,
    LUIOp,
    LIOp,
    AUIPCOp,
    XOROp,
    XORIOp,
    OROp,
    ORIOp,
    ANDOp,
    ANDIOp,
    SLTOp,
    SLTIOp,
    SLTUOp,
    SLTIUOp,
    JOp,
    JALOp,
    JALROp,
    ECALLOp,
    EBREAKOp,
    MULOp,
    MULHOp,
    MULHSUOp,
    MULHUOp,
    DIVOp,
    DIVUOp,
    REMOp,
    REMUOp,
    LabelOp,
    CallOp,
    AllocOp,
    FuncOp,
    ReturnOp,
]
RISCVSSA = Dialect(riscv_ssa_ops, riscv_ssa_attrs)
