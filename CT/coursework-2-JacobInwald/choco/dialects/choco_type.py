from __future__ import annotations

from xdsl.dialects.builtin import StringAttr
from xdsl.ir import Attribute, ParametrizedAttribute, TypeAttribute
from xdsl.irdl import ParameterDef, irdl_attr_definition


@irdl_attr_definition
class NamedType(ParametrizedAttribute, TypeAttribute):
    name = "choco.ir.named_type"

    type_name: ParameterDef[StringAttr]


@irdl_attr_definition
class ListType(ParametrizedAttribute, TypeAttribute):
    name = "choco.ir.list_type"

    elem_type: ParameterDef[Attribute]


int_type = NamedType([StringAttr("int")])
bool_type = NamedType([StringAttr("bool")])
str_type = NamedType([StringAttr("str")])
none_type = NamedType([StringAttr("<None>")])
empty_type = NamedType([StringAttr("<Empty>")])
object_type = NamedType([StringAttr("object")])
