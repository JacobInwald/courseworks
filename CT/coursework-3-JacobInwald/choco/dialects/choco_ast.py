from __future__ import annotations

from typing import List, Optional, Type, Union

from xdsl.dialects.builtin import IntegerAttr, IntegerType, StringAttr
from xdsl.ir import (
    Attribute,
    Block,
    Data,
    Dialect,
    Operation,
    ParametrizedAttribute,
    Region,
)
from xdsl.irdl import (
    IRDLOperation,
    irdl_attr_definition,
    irdl_op_definition,
    opt_prop_def,
    prop_def,
    region_def,
)
from xdsl.parser import BaseParser
from xdsl.printer import Printer
from xdsl.traits import (
    NoTerminator,
)

from choco.dialects import choco_type


def get_type(annotation: str) -> Operation:
    return TypeName(annotation)


def get_statement_op_types() -> List[Type[Operation]]:
    statements: List[Type[Operation]] = [If, While, For, Pass, Return, Assign]
    return statements + get_expression_op_types()


def get_expression_op_types() -> List[Type[Operation]]:
    return [
        UnaryExpr,
        BinaryExpr,
        IfExpr,
        ExprName,
        ListExpr,
        IndexExpr,
        CallExpr,
        Literal,
    ]


def get_type_op_types() -> List[Type[Operation]]:
    return [TypeName, ListType]


@irdl_op_definition
class Program(IRDLOperation):
    name = "choco.ast.program"

    # [VarDef | FuncDef]*
    defs: Region = region_def("single_block")

    # Stmt*
    stmts: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, defs: List[Operation], stmts: List[Operation]) -> None:
        super().__init__(regions=[Region([Block(defs)]), Region([Block(stmts)])])

    def verify_(self) -> None:
        for def_ in self.defs.blocks[0].ops:
            if type(def_) not in [VarDef, FuncDef]:
                raise Exception(
                    f"{Program.name} first region expects {VarDef.name} "
                    f"and {FuncDef.name} operations, but got {def_.name}"
                )
        for stmt in self.stmts.blocks[0].ops:
            if type(stmt) not in get_statement_op_types():
                raise Exception(
                    f"{Program.name} second region only expects "
                    f"statements operations, but got {stmt.name}"
                )


@irdl_op_definition
class FuncDef(IRDLOperation):
    name = "choco.ast.func_def"

    func_name: StringAttr = prop_def(StringAttr)
    params: Region = region_def("single_block")
    return_type: Region = region_def("single_block")

    # [GlobalDecl | NonLocalDecl | VarDef ]* Stmt+
    func_body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(
        self,
        func_name: Union[str, StringAttr],
        params: List[Operation],
        return_type: Operation,
        func_body: List[Operation],
    ) -> None:
        if isinstance(func_name, str):
            func_name = StringAttr(func_name)
        super().__init__(
            properties={"func_name": func_name},
            regions=[
                Region([Block(params)]),
                Region([Block([return_type])]),
                func_body,
            ],
        )

    def verify_(self) -> None:
        for param in self.params.blocks[0].ops:
            if not isinstance(param, TypedVar):
                raise Exception(
                    f"{FuncDef.name} first region expects {TypedVar.name} "
                    f"operations, but got {param.name}."
                )
        return_type = self.return_type.blocks[0].ops
        if len(return_type) != 1:
            raise Exception(f"{FuncDef.name} expects a single return type")
        if return_type.first is None:
            raise Exception(f"{FuncDef.name} type is empty!")
        if type(return_type.first) not in get_type_op_types():
            raise Exception(
                f"{FuncDef.name} second region expects a single operation "
                f"representing a type, but got {return_type.first.name}."
            )
        stmt_region = False
        for stmt in self.func_body.blocks[0].ops:
            if not stmt_region:
                if type(stmt) in [GlobalDecl, NonLocalDecl, VarDef]:
                    continue
                else:
                    stmt_region = True
            if stmt_region:
                if not type(stmt) in get_statement_op_types():
                    raise Exception(
                        f"{FuncDef.name} third region expects variable declarations "
                        f"followed by statements, but got {stmt.name}"
                    )


@irdl_op_definition
class TypedVar(IRDLOperation):
    name = "choco.ast.typed_var"

    var_name: StringAttr = prop_def(StringAttr)
    type: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, var_name: str | StringAttr, type_: Operation) -> None:
        if isinstance(var_name, str):
            var_name = StringAttr(var_name)
        super().__init__(regions=[[type_]], properties={"var_name": var_name})

    def verify_(self) -> None:
        typ = self.type.blocks[0].ops
        if len(typ) != 1 or type(typ.first) not in get_type_op_types():
            raise Exception(
                f"{TypedVar.name} second region expects a single operation representing a type, but got {typ}."
            )


@irdl_op_definition
class TypeName(IRDLOperation):
    name = "choco.ast.type_name"

    type_name: StringAttr = prop_def(StringAttr)

    def __init__(self, type_name: str | StringAttr) -> None:
        if isinstance(type_name, str):
            type_name = StringAttr(type_name)
        super().__init__(properties={"type_name": type_name})

    def verify_(self) -> None:
        legal_type_names = ["object", "int", "bool", "str", "<None>"]
        if self.type_name.data not in legal_type_names:  # type: ignore
            raise Exception(
                f"{self.name} expects type name, but got '{self.type_name.data}'"  # type: ignore
            )


@irdl_op_definition
class ListType(IRDLOperation):
    name = "choco.ast.list_type"

    elem_type: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, elem_type: Operation) -> None:
        super().__init__(regions=[[elem_type]])

    def verify_(self) -> None:
        elem_type = self.elem_type.blocks[0].ops
        if len(elem_type) != 1 or type(elem_type.first) not in get_type_op_types():
            raise Exception(
                f"{ListType.name} operation expects a single type operation in the first region."
            )


@irdl_op_definition
class GlobalDecl(IRDLOperation):
    name = "choco.ast.global_decl"

    decl_name: StringAttr = prop_def(StringAttr)

    def __init__(self, decl_name: Union[str, StringAttr]) -> None:
        if isinstance(decl_name, str):
            decl_name = StringAttr(decl_name)
        super().__init__(properties={"decl_name": decl_name})


@irdl_op_definition
class NonLocalDecl(IRDLOperation):
    name = "choco.ast.nonlocal_decl"

    decl_name: StringAttr = prop_def(StringAttr)

    def __init__(self, decl_name: Union[str, StringAttr]) -> None:
        if isinstance(decl_name, str):
            decl_name = StringAttr(decl_name)
        super().__init__(properties={"decl_name": decl_name})


@irdl_op_definition
class VarDef(IRDLOperation):
    name = "choco.ast.var_def"

    typed_var: Region = region_def("single_block")
    literal: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, typed_var: Operation, literal: Operation) -> None:
        super().__init__(regions=[[typed_var], [literal]])

    def verify_(self) -> None:
        elem_type = self.typed_var.blocks[0].ops
        if len(elem_type) != 1 or not isinstance(elem_type.first, TypedVar):
            raise Exception(
                f"{VarDef.name} operation expects a single {TypedVar.name} operation in the first region."
            )
        literal = self.literal.blocks[0].ops
        if len(literal) != 1 or not isinstance(literal.first, Literal):
            raise Exception(
                f"{VarDef.name} operation expects a single {Literal.name} operation in the second region."
            )


# Statements


@irdl_op_definition
class If(IRDLOperation):
    name = "choco.ast.if"

    cond: Region = region_def("single_block")
    then: Region = region_def("single_block")
    orelse: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(
        self,
        cond: Operation,
        then: List[Operation],
        orelse: List[Operation],
    ) -> None:
        super().__init__(
            regions=[
                Region([Block([cond])]),
                Region([Block(then)]),
                Region([Block(orelse)]),
            ]
        )

    def verify_(self) -> None:
        cond = self.cond.blocks[0].ops
        if len(cond) != 1 or type(cond.first) not in get_expression_op_types():
            raise Exception(
                f"{If.name} operation expects a single expression in the first region."
            )
        for expr in self.then.blocks[0].ops:
            if type(expr) not in get_statement_op_types():
                raise Exception(
                    f"{If.name} operation expects statements operations in the second region."
                )
        for expr in self.orelse.blocks[0].ops:
            if type(expr) not in get_statement_op_types():
                raise Exception(
                    f"{If.name} operation expects statements operations in the third region."
                )


@irdl_op_definition
class While(IRDLOperation):
    name = "choco.ast.while"

    cond: Region = region_def("single_block")
    body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, cond: Operation, body: List[Operation]) -> None:
        super().__init__(regions=[[cond], body])

    def verify_(self) -> None:
        cond = self.cond.blocks[0].ops
        if len(cond) != 1 or type(cond.first) not in get_expression_op_types():
            raise Exception(
                f"{While.name} operation expects a single expression in the first region."
            )
        for stmt in self.body.blocks[0].ops:
            if type(stmt) not in get_statement_op_types():
                raise Exception(
                    f"{While.name} operation expects statements operations in the second region."
                )


@irdl_op_definition
class For(IRDLOperation):
    name = "choco.ast.for"

    iter_name: StringAttr = prop_def(StringAttr)
    iter: Region = region_def("single_block")
    body: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(
        self, iter_name: Union[str, StringAttr], iter_: Operation, body: List[Operation]
    ) -> None:
        if isinstance(iter_name, str):
            iter_name = StringAttr(iter_name)
        super().__init__(properties={"iter_name": iter_name}, regions=[[iter_], body])

    def verify_(self) -> None:
        iter = self.iter.blocks[0].ops
        if len(iter) != 1 or type(iter.first) not in get_expression_op_types():
            raise Exception(
                f"{For.name} operation expects a single expression in the first region."
            )
        for stmt in self.body.blocks[0].ops:
            if type(stmt) not in get_statement_op_types():
                raise Exception(
                    f"{For.name} operation expects statements operations in the second region."
                )


@irdl_op_definition
class Pass(IRDLOperation):
    name = "choco.ast.pass"

    def __init__(self) -> None:
        super().__init__()


@irdl_op_definition
class Return(IRDLOperation):
    name = "choco.ast.return"

    value: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, value: Optional[Operation]) -> None:
        super().__init__(
            regions=[Region([Block([value] if value is not None else [])])]
        )

    def verify_(self) -> None:
        value = self.value.blocks[0].ops
        if len(value) > 1 or (
            len(value) == 1 and type(value.first) not in get_expression_op_types()
        ):
            raise Exception(
                f"{Return.name} operation expects a single expression in the first region."
            )


@irdl_op_definition
class Assign(IRDLOperation):
    name = "choco.ast.assign"

    target: Region = region_def("single_block")
    value: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])

    def __init__(self, target: Operation, value: Operation) -> None:
        super().__init__(regions=[[target], [value]])

    def verify_(self) -> None:
        target = self.target.blocks[0].ops
        if len(target) != 1 or type(target.first) not in get_expression_op_types():
            raise Exception(
                f"{Assign.name} operation expects a single expression in the first region, but get {target}."
            )
        for expr in self.value.blocks[0].ops:
            if type(expr) not in get_expression_op_types() + [Assign]:
                raise Exception(
                    f"{Assign.name} operation expects a single expression, or a single {Assign.name} operation in the "
                    f"second region."
                )


# Expressions


@irdl_attr_definition
class BoolAttr(Data[bool]):
    name = "choco.ast.bool"

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
        return BoolAttr(val)  # type: ignore


@irdl_attr_definition
class NoneAttr(ParametrizedAttribute):
    name = "choco.ast.none"


@irdl_op_definition
class Literal(IRDLOperation):
    name = "choco.ast.literal"

    value: StringAttr | IntegerAttr[IntegerType] | BoolAttr | NoneAttr = prop_def(
        StringAttr | IntegerAttr[IntegerType] | BoolAttr | NoneAttr
    )
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(self, value: Union[None, bool, int, str]) -> None:
        if value is None:
            attr = NoneAttr()
        elif type(value) is bool:
            attr = BoolAttr.from_bool(value)
        elif type(value) is int:
            attr = IntegerAttr.from_int_and_width(value, 32)
        elif type(value) is str:
            attr = StringAttr(value)
        else:
            raise Exception(f"Unknown literal of type {type(value)}")
        super().__init__(properties={"value": attr})


@irdl_op_definition
class ExprName(IRDLOperation):
    name = "choco.ast.id_expr"

    id: StringAttr = prop_def(StringAttr)
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(self, name: Union[str, StringAttr]) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        super().__init__(properties={"id": name})


@irdl_op_definition
class UnaryExpr(IRDLOperation):
    name = "choco.ast.unary_expr"

    op: StringAttr = prop_def(StringAttr)
    value: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    @staticmethod
    def get_valid_ops() -> List[str]:
        return ["-", "not"]

    def __init__(self, op: Union[str, StringAttr], value: Operation) -> None:
        if isinstance(op, str):
            op = StringAttr(op)
        super().__init__(properties={"op": op}, regions=[[value]])

    def verify_(self) -> None:
        if self.op.data not in self.get_valid_ops():  # type: ignore
            raise Exception(
                f"Unsupported unary expression: '{self.op.data}'."  # type: ignore
            )
        value = self.value.blocks[0].ops
        if len(value) != 1 or type(value.first) not in get_expression_op_types():
            raise Exception(
                f"{UnaryExpr.name} operation expects a single expression in the first region."
            )


@irdl_op_definition
class BinaryExpr(IRDLOperation):
    name = "choco.ast.binary_expr"

    op: StringAttr = prop_def(StringAttr)
    lhs: Region = region_def("single_block")
    rhs: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    @staticmethod
    def get_valid_ops() -> List[str]:
        return [
            "+",
            "-",
            "*",
            "//",
            "%",
            "and",
            "is",
            "or",
            ">",
            "<",
            "==",
            "!=",
            ">=",
            "<=",
        ]

    def __init__(
        self,
        op: str | StringAttr,
        lhs: Operation,
        rhs: Operation,
    ) -> None:
        if isinstance(op, str):
            op = StringAttr(op)
        super().__init__(properties={"op": op}, regions=[[lhs], [rhs]])

    def verify_(self) -> None:
        if self.op.data not in self.get_valid_ops():  # type: ignore
            raise Exception(
                f"Unsupported unary expression: '{self.op.data}'."  # type: ignore
            )
        lhs = self.lhs.blocks[0].ops
        if len(lhs) != 1 or type(lhs.first) not in get_expression_op_types():
            raise Exception(
                f"{BinaryExpr.name} operation expects a single expression in the first region."
            )
        rhs = self.rhs.blocks[0].ops
        if len(rhs) != 1 or type(rhs.first) not in get_expression_op_types():
            raise Exception(
                f"{BinaryExpr.name} operation expects a single expression in the second region."
            )


@irdl_op_definition
class IfExpr(IRDLOperation):
    name = "choco.ast.if_expr"

    cond: Region = region_def("single_block")
    then: Region = region_def("single_block")
    or_else: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(
        self,
        cond: Operation,
        then: Operation,
        or_else: Operation,
    ) -> None:
        super().__init__(regions=[[cond], [then], [or_else]])

    def verify_(self) -> None:
        cond = self.cond.blocks[0].ops
        if len(cond) != 1 or type(cond.first) not in get_expression_op_types():
            raise Exception(
                f"{IfExpr.name} operation expects a single expression in the first region."
            )
        then = self.then.blocks[0].ops
        if len(then) != 1 or type(then.first) not in get_expression_op_types():
            raise Exception(
                f"{IfExpr.name} operation expects a single expression in the second region."
            )
        or_else = self.or_else.blocks[0].ops
        if len(or_else) != 1 or type(or_else.first) not in get_expression_op_types():
            raise Exception(
                f"{IfExpr.name} operation expects a single expression in the third region."
            )


@irdl_op_definition
class ListExpr(IRDLOperation):
    name = "choco.ast.list_expr"

    elems: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(self, elems: List[Operation]) -> None:
        super().__init__(regions=[Region([Block(elems)])])

    def verify_(self) -> None:
        for expr in self.elems.blocks[0].ops:
            if type(expr) not in get_expression_op_types():
                raise Exception(
                    f"{ListExpr.name} operation expects expression operations in the first region."
                )


@irdl_op_definition
class CallExpr(IRDLOperation):
    name = "choco.ast.call_expr"

    func: StringAttr = prop_def(StringAttr)
    args: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(self, func: str | StringAttr, args: List[Operation]) -> None:
        if isinstance(func, str):
            func = StringAttr(func)
        super().__init__(regions=[Region([Block(args)])], properties={"func": func})

    def verify_(self) -> None:
        for arg in self.args.blocks[0].ops:
            if type(arg) not in get_expression_op_types():
                raise Exception(
                    f"{CallExpr.name} operation expects expression operations in the second region."
                )


@irdl_op_definition
class IndexExpr(IRDLOperation):
    name = "choco.ast.index_expr"

    value: Region = region_def("single_block")
    index: Region = region_def("single_block")

    traits = frozenset([NoTerminator()])
    type_hint: Attribute | None = opt_prop_def(Attribute)

    def __init__(self, value: Operation, index: Operation) -> None:
        super().__init__(regions=[[value], [index]])

    def verify_(self) -> None:
        value = self.value.blocks[0].ops
        if len(value) != 1 or type(value.first) not in get_expression_op_types():
            raise Exception(
                f"{IndexExpr.name} operation expects a single expression operation in the first region."
            )
        index = self.index.blocks[0].ops
        if len(index) != 1 or type(index.first) not in get_expression_op_types():
            raise Exception(
                f"{IndexExpr.name} operation expects a single expression operation in the first region."
            )


ast_attrs: List[Type[Attribute]] = [
    choco_type.NamedType,
    choco_type.ListType,
    BoolAttr,
    NoneAttr,
]

ast_ops: List[Type[Operation]] = [
    Program,
    FuncDef,
    TypedVar,
    TypeName,
    ListType,
    GlobalDecl,
    NonLocalDecl,
    VarDef,
    If,
    While,
    For,
    Pass,
    Return,
    Assign,
    Literal,
    ExprName,
    UnaryExpr,
    BinaryExpr,
    IfExpr,
    ListExpr,
    CallExpr,
    IndexExpr,
]
ChocoAST = Dialect(ast_ops, ast_attrs)
