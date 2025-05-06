// RUN: choco-opt -p "choco-ast-to-choco-flat" %s | filecheck %s

//
// l1: [int] = None
// l2: [str] = None
// l3: [object] = None
// l1 = [1,2,3]
// l2 = ["1","2","3"]
// l3 = l1 + l2
//

builtin.module {
  "choco.ast.program"() ({
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "l1"}> ({
        "choco.ast.list_type"() ({
          "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
        }) : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = #choco.ast.none, "type_hint" = !choco.ir.named_type<"<None>">}> : () -> ()
    }) : () -> ()
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "l2"}> ({
        "choco.ast.list_type"() ({
          "choco.ast.type_name"() <{"type_name" = "str"}> : () -> ()
        }) : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = #choco.ast.none, "type_hint" = !choco.ir.named_type<"<None>">}> : () -> ()
    }) : () -> ()
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "l3"}> ({
        "choco.ast.list_type"() ({
          "choco.ast.type_name"() <{"type_name" = "object"}> : () -> ()
        }) : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = #choco.ast.none, "type_hint" = !choco.ir.named_type<"<None>">}> : () -> ()
    }) : () -> ()
  }, {
    "choco.ast.assign"() ({
      "choco.ast.id_expr"() <{"id" = "l1", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> : () -> ()
    }, {
      "choco.ast.list_expr"() <{"type_hint" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> ({
        "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
        "choco.ast.literal"() <{"value" = 2 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
        "choco.ast.literal"() <{"value" = 3 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
      }) : () -> ()
    }) : () -> ()
    "choco.ast.assign"() ({
      "choco.ast.id_expr"() <{"id" = "l2", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> ()
    }, {
      "choco.ast.list_expr"() <{"type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> ({
        "choco.ast.literal"() <{"value" = "1", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "2", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "3", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
      }) : () -> ()
    }) : () -> ()
    "choco.ast.assign"() ({
      "choco.ast.id_expr"() <{"id" = "l3", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"object">>}> : () -> ()
    }, {
      "choco.ast.binary_expr"() <{"op" = "+", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"object">>}> ({
        "choco.ast.id_expr"() <{"id" = "l1", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> : () -> ()
      }, {
        "choco.ast.id_expr"() <{"id" = "l2", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> ()
      }) : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:     %1 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>
// CHECK-NEXT:     "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>, !choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     %2 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:     %3 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>
// CHECK-NEXT:     "choco.ir.store"(%3, %2) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>, !choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     %4 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:     %5 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"object">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"object">>>
// CHECK-NEXT:     "choco.ir.store"(%5, %4) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"object">>>, !choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     %6 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %7 = "choco.ir.literal"() <{"value" = 2 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %8 = "choco.ir.literal"() <{"value" = 3 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %9 = "choco.ir.list_expr"(%6, %7, %8) : (!choco.ir.named_type<"int">, !choco.ir.named_type<"int">, !choco.ir.named_type<"int">) -> !choco.ir.list_type<!choco.ir.named_type<"int">>
// CHECK-NEXT:     "choco.ir.store"(%1, %9) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>, !choco.ir.list_type<!choco.ir.named_type<"int">>) -> ()
// CHECK-NEXT:     %10 = "choco.ir.literal"() <{"value" = "1"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %11 = "choco.ir.literal"() <{"value" = "2"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %12 = "choco.ir.literal"() <{"value" = "3"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %13 = "choco.ir.list_expr"(%10, %11, %12) : (!choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">) -> !choco.ir.list_type<!choco.ir.named_type<"str">>
// CHECK-NEXT:     "choco.ir.store"(%3, %13) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>, !choco.ir.list_type<!choco.ir.named_type<"str">>) -> ()
// CHECK-NEXT:     %14 = "choco.ir.load"(%1) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>) -> !choco.ir.list_type<!choco.ir.named_type<"int">>
// CHECK-NEXT:     %15 = "choco.ir.load"(%3) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>) -> !choco.ir.list_type<!choco.ir.named_type<"str">>
// CHECK-NEXT:     %16 = "choco.ir.binary_expr"(%14, %15) <{"op" = "+"}> : (!choco.ir.list_type<!choco.ir.named_type<"int">>, !choco.ir.list_type<!choco.ir.named_type<"str">>) -> !choco.ir.list_type<!choco.ir.named_type<"object">>
// CHECK-NEXT:     "choco.ir.store"(%5, %16) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"object">>>, !choco.ir.list_type<!choco.ir.named_type<"object">>) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
