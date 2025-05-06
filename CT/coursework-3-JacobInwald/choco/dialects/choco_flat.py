from __future__ import annotations

from io import StringIO
from typing import List, Type, Union

from xdsl.dialects.builtin import IntegerAttr, StringAttr
from xdsl.ir import (
    Attribute,
    Data,
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
    OptOpResult,
    ParameterDef,
    Region,
    VarOperand,
    irdl_attr_definition,
    irdl_op_definition,
    operand_def,
    opt_prop_def,
    opt_result_def,
    prop_def,
    region_def,
    result_def,
    var_operand_def,
)
from xdsl.parser import BaseParser
from xdsl.printer import Printer
from xdsl.traits import (
    NoTerminator,
)
from xdsl.utils.diagnostic import Diagnostic

from choco.dialects import choco_type
from choco.dialects.choco_type import ListType, bool_type, int_type, none_type, str_type


def error(op: Operation, msg: str):
    diag = Diagnostic()
    diag.add_message(op, msg)
    diag.raise_exception(f"{op.name} operation does not verify", op)


@irdl_attr_definition
class BoolAttr(Data[bool]):
    name = "choco.ir.bool"

    @classmethod
    def parse_parameter(cls, parser: BaseParser) -> bool:
        if parser.parse_optional_keyword("True"):
            return True
        if parser.parse_optional_keyword("False"):
            return False
        parser.raise_error("Expected True or False literal")

    def print_parameter(self, printer: Printer) -> None:
        printer.print_string(str(self.data))

    @staticmethod
    def from_bool(val: bool) -> BoolAttr:
        return BoolAttr(val)


@irdl_attr_definition
class NoneAttr(ParametrizedAttribute):
    name = "choco.ir.none"


@irdl_op_definition
class ClassDef(IRDLOperation):
    name = "choco.ir.class_def"

    class_name: StringAttr = prop_def(StringAttr)
    super_class_name: StringAttr = prop_def(StringAttr)
    class_body: Region = region_def("single_block")


@irdl_op_definition
class FuncDef(IRDLOperation):
    name = "choco.ir.func_def"

    func_name: StringAttr = prop_def(StringAttr)
    return_type: Attribute = prop_def(Attribute)
    func_body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])


# Statements


@irdl_op_definition
class If(IRDLOperation):
    name = "choco.ir.if"

    cond: Operand = operand_def(choco_type.bool_type)
    then: Region = region_def("single_block")
    orelse: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class While(IRDLOperation):
    name = "choco.ir.while"

    cond: Region = region_def("single_block")
    body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    @property
    def cond_ssa_value(self) -> SSAValue:
        yield_ = self.cond.ops.last
        assert isinstance(yield_, Yield)
        return yield_.value  # type: ignore

    def verify_(self) -> None:
        yield_ = self.cond.ops.last
        if not isinstance(yield_, Yield):
            raise Exception(
                f"{While.name} operation expects last operation in condition to be a {Yield.name}"
            )
        if not (yield_.value.type == bool_type):  # type: ignore
            raise Exception(
                f"{While.name} operation expects last operation in condition to have type {bool_type.name}"
            )


@irdl_op_definition
class For(IRDLOperation):
    name = "choco.ir.for"

    iter_: Operand = operand_def(Attribute)
    target: Operand = operand_def(Attribute)
    body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class Pass(IRDLOperation):
    name = "choco.ir.pass"


@irdl_op_definition
class Return(IRDLOperation):
    name = "choco.ir.return"

    value: Operand = operand_def(Attribute)


@irdl_op_definition
class Yield(IRDLOperation):
    name = "choco.ir.yield"

    value: Operand = operand_def(Attribute)

    @staticmethod
    def get(value: Union[SSAValue, Operation]) -> Yield:
        return Yield.build(operands=[value])


@irdl_op_definition
class Assign(IRDLOperation):
    name = "choco.ir.assign"

    target: Operand = operand_def(Attribute)
    value: Operand = operand_def(Attribute)

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        from riscv.ssa_dialect import RegisterType

        if isinstance(self.target.type, RegisterType) or isinstance(  # type: ignore
            self.value.type, RegisterType  # type: ignore
        ):
            # TODO: I don't know what to do here, so I pass
            pass
        else:
            from choco.type_checking import Type, check_assignment_compatibility

            target_type = Type.from_attribute(self.target.type)  # type: ignore
            value_type = Type.from_attribute(self.value.type)  # type: ignore
            check_assignment_compatibility(value_type, target_type)


# Expressions


@irdl_op_definition
class Literal(IRDLOperation):
    name = "choco.ir.literal"

    value: Attribute = prop_def(Attribute)
    result: OpResult = result_def()

    @staticmethod
    def get(value: Union[None, bool, int, str], verify_op: bool = True) -> Literal:
        if value is None:
            attr = NoneAttr()
            ty = none_type
        elif type(value) is bool:
            attr = BoolAttr.from_bool(value)
            ty = bool_type
        elif type(value) is int:
            attr = IntegerAttr.from_int_and_width(value, 32)
            ty = int_type
        elif type(value) is str:
            attr = StringAttr(value)
            ty = str_type
        else:
            raise Exception(f"Unknown literal of type {type(value)}")

        res = Literal.build(operands=[], properties={"value": attr}, result_types=[ty])
        if verify_op:
            # We don't verify nested operations since they might have already been verified
            res.verify(verify_nested_ops=False)
        return res


@irdl_op_definition
class UnaryExpr(IRDLOperation):
    name = "choco.ir.unary_expr"

    op: StringAttr = prop_def(StringAttr)
    value: Operand = operand_def(Attribute)
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class BinaryExpr(IRDLOperation):
    name = "choco.ir.binary_expr"

    op: StringAttr = prop_def(StringAttr)
    lhs: Operand = operand_def(Attribute)
    rhs: Operand = operand_def(Attribute)
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class EffectfulBinaryExpr(IRDLOperation):
    name = "choco.ir.effectful_binary_expr"

    op: StringAttr = prop_def(StringAttr)
    lhs: Region = region_def("single_block")
    rhs: Region = region_def("single_block")
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class IfExpr(IRDLOperation):
    name = "choco.ir.if_expr"

    cond: Operand = operand_def(choco_type.bool_type)
    then: Region = region_def("single_block")
    or_else: Region = region_def("single_block")
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])

    @property
    def then_ssa_value(self) -> SSAValue:
        then_ = self.then.ops.last
        assert isinstance(then_, Yield)
        return then_.value  # type: ignore

    @property
    def or_else_ssa_value(self) -> SSAValue:
        or_else_ = self.or_else.ops.last
        assert isinstance(or_else_, Yield)
        return or_else_.value  # type: ignore

    def verif_(self) -> None:
        then_ = self.then.ops
        if not isinstance(then_.last, Yield):
            raise Exception(
                f"{IfExpr.name} operation expects last operation in then branch to be a {Yield.name}"
            )
        or_else_ = self.or_else.ops
        if not isinstance(or_else_.last, Yield):
            raise Exception(
                f"{IfExpr.name} operation expects last operation in or else branch to be a {Yield.name}"
            )


@irdl_op_definition
class ListExpr(IRDLOperation):
    name = "choco.ir.list_expr"

    elems: VarOperand = var_operand_def()
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])


@irdl_op_definition
class CallExpr(IRDLOperation):
    name = "choco.ir.call_expr"

    args: VarOperand = var_operand_def()
    func_name: Attribute = prop_def(Attribute)
    result: OptOpResult = opt_result_def()

    type_hint: Attribute | None = opt_prop_def(Attribute)


@irdl_op_definition
class MemberExpr(IRDLOperation):
    name = "choco.ir.member_expr"

    value: Operand = operand_def(Attribute)
    attribute: StringAttr = prop_def(StringAttr)
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])


# Memory operations


@irdl_attr_definition
class MemlocType(ParametrizedAttribute, TypeAttribute):
    name = "choco.ir.memloc"

    type: ParameterDef[choco_type.NamedType | choco_type.ListType]


@irdl_op_definition
class Alloc(IRDLOperation):
    name = "choco.ir.alloc"

    type: choco_type.NamedType | choco_type.ListType = prop_def(
        choco_type.NamedType | choco_type.ListType
    )
    memloc: OpResult = result_def(MemlocType)

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        if self.type != self.memloc.type.type:  # type: ignore
            error(self, "expected types to match")


@irdl_op_definition
class IndexString(IRDLOperation):
    name = "choco.ir.index_string"

    value: Operand = operand_def(Attribute)
    index: Operand = operand_def(choco_type.int_type)
    result: OpResult = result_def(MemlocType)

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        if isinstance(self.value.type, ListType):  # type: ignore
            if self.value.type.elem_type != self.result.type.type:  # type: ignore
                error(self, "expected types to match")
        elif self.value.type == choco_type.str_type:  # type: ignore
            if self.result.type.type != choco_type.str_type:  # type: ignore
                error(self, "expected types to match")
        else:
            error(self, "expected List of String type")


@irdl_op_definition
class GetAddress(IRDLOperation):
    name = "choco.ir.get_address"

    value: Operand = operand_def(Attribute)
    index: Operand = operand_def(choco_type.int_type)
    result: OpResult = result_def(MemlocType)

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        if isinstance(self.value.type, ListType):  # type: ignore
            if self.value.type.elem_type != self.result.type.type:  # type: ignore
                error(self, "expected types to match")
        elif self.value.type == choco_type.str_type:  # type: ignore
            if self.result.type.type != choco_type.str_type:  # type: ignore
                error(self, "expected types to match")
        else:
            error(self, "expected List of String type")


@irdl_op_definition
class Load(IRDLOperation):
    name = "choco.ir.load"

    memloc: Operand = operand_def(MemlocType)
    result: OpResult = result_def()

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        if self.result.type != self.memloc.type.type:  # type: ignore
            sio = StringIO()
            p = Printer(stream=sio)
            p.print_attribute(self.result.type)  # type: ignore
            type_str = sio.getvalue()

            error(
                self,
                f"Mismatched operand types! Should the first operand be of type !choco.ir.memloc<{type_str}>?",
            )


@irdl_op_definition
class Store(IRDLOperation):
    name = "choco.ir.store"

    memloc: Operand = operand_def(MemlocType)
    value: Operand = operand_def(Attribute)

    traits = frozenset([NoTerminator()])

    def verify_(self) -> None:
        if self.value.type != self.memloc.type.type:  # type: ignore
            if isinstance(self.memloc.type.type, choco_type.ListType):  # type: ignore
                if self.value.type in [choco_type.empty_type, choco_type.none_type]:  # type: ignore
                    return
            if self.memloc.type.type == choco_type.object_type:  # type: ignore
                return
            sio = StringIO()
            p = Printer(stream=sio)
            p.print_attribute(self.value.type)  # type: ignore
            type_str = sio.getvalue()

            error(
                self,
                f"Mismatched operand types! Should the first operand be of type !choco.ir.memloc<{type_str}>?",
            )


choco_flat_attrs: List[Type[Attribute]] = [NoneAttr, BoolAttr, MemlocType]
choco_flat_ops: List[Type[Operation]] = [
    ClassDef,
    FuncDef,
    If,
    While,
    For,
    Pass,
    Return,
    Assign,
    Literal,
    UnaryExpr,
    BinaryExpr,
    EffectfulBinaryExpr,
    IfExpr,
    ListExpr,
    CallExpr,
    MemberExpr,
    Alloc,
    GetAddress,
    IndexString,
    Load,
    Store,
    Yield,
]

ChocoFlat = Dialect(choco_flat_ops, choco_flat_attrs)
