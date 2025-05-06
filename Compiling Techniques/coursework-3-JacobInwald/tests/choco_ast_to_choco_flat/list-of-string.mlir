// RUN: choco-opt -p "choco-ast-to-choco-flat" %s | filecheck %s

//
// l: [str] = None
// s: str = ""
//
// l = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
// s = s + l[0]
// print(s)
//

builtin.module {
  "choco.ast.program"() ({
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "l"}> ({
        "choco.ast.list_type"() ({
          "choco.ast.type_name"() <{"type_name" = "str"}> : () -> ()
        }) : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = #choco.ast.none, "type_hint" = !choco.ir.named_type<"<None>">}> : () -> ()
    }) : () -> ()
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "s"}> ({
        "choco.ast.type_name"() <{"type_name" = "str"}> : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = "", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
    }) : () -> ()
  }, {
    "choco.ast.assign"() ({
      "choco.ast.id_expr"() <{"id" = "l", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> ()
    }, {
      "choco.ast.list_expr"() <{"type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> ({
        "choco.ast.literal"() <{"value" = "0", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "1", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "2", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "3", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "4", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "5", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "6", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "7", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "8", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
        "choco.ast.literal"() <{"value" = "9", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
      }) : () -> ()
    }) : () -> ()
    "choco.ast.assign"() ({
      "choco.ast.id_expr"() <{"id" = "s", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
    }, {
      "choco.ast.binary_expr"() <{"op" = "+", "type_hint" = !choco.ir.named_type<"str">}> ({
        "choco.ast.id_expr"() <{"id" = "s", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
      }, {
        "choco.ast.index_expr"() <{"type_hint" = !choco.ir.named_type<"str">}> ({
          "choco.ast.id_expr"() <{"id" = "l", "type_hint" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> ()
        }, {
          "choco.ast.literal"() <{"value" = 0 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
        }) : () -> ()
      }) : () -> ()
    }) : () -> ()
    "choco.ast.call_expr"() <{"func" = "print", "type_hint" = !choco.ir.named_type<"<None>">}> ({
      "choco.ast.id_expr"() <{"id" = "s", "type_hint" = !choco.ir.named_type<"str">}> : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:     %1 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"str">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>
// CHECK-NEXT:     "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>, !choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     %2 = "choco.ir.literal"() <{"value" = ""}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %3 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"str">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"str">>
// CHECK-NEXT:     "choco.ir.store"(%3, %2) : (!choco.ir.memloc<!choco.ir.named_type<"str">>, !choco.ir.named_type<"str">) -> ()
// CHECK-NEXT:     %4 = "choco.ir.literal"() <{"value" = "0"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %5 = "choco.ir.literal"() <{"value" = "1"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %6 = "choco.ir.literal"() <{"value" = "2"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %7 = "choco.ir.literal"() <{"value" = "3"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %8 = "choco.ir.literal"() <{"value" = "4"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %9 = "choco.ir.literal"() <{"value" = "5"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %10 = "choco.ir.literal"() <{"value" = "6"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %11 = "choco.ir.literal"() <{"value" = "7"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %12 = "choco.ir.literal"() <{"value" = "8"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %13 = "choco.ir.literal"() <{"value" = "9"}> : () -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %14 = "choco.ir.list_expr"(%4, %5, %6, %7, %8, %9, %10, %11, %12, %13) : (!choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">, !choco.ir.named_type<"str">) -> !choco.ir.list_type<!choco.ir.named_type<"str">>
// CHECK-NEXT:     "choco.ir.store"(%1, %14) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>, !choco.ir.list_type<!choco.ir.named_type<"str">>) -> ()
// CHECK-NEXT:     %15 = "choco.ir.load"(%3) : (!choco.ir.memloc<!choco.ir.named_type<"str">>) -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %16 = "choco.ir.load"(%1) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"str">>>) -> !choco.ir.list_type<!choco.ir.named_type<"str">>
// CHECK-NEXT:     %17 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %18 = "choco.ir.get_address"(%16, %17) : (!choco.ir.list_type<!choco.ir.named_type<"str">>, !choco.ir.named_type<"int">) -> !choco.ir.memloc<!choco.ir.named_type<"str">>
// CHECK-NEXT:     %19 = "choco.ir.load"(%18) : (!choco.ir.memloc<!choco.ir.named_type<"str">>) -> !choco.ir.named_type<"str">
// CHECK-NEXT:     %20 = "choco.ir.binary_expr"(%15, %19) <{"op" = "+"}> : (!choco.ir.named_type<"str">, !choco.ir.named_type<"str">) -> !choco.ir.named_type<"str">
// CHECK-NEXT:     "choco.ir.store"(%3, %20) : (!choco.ir.memloc<!choco.ir.named_type<"str">>, !choco.ir.named_type<"str">) -> ()
// CHECK-NEXT:     %21 = "choco.ir.load"(%3) : (!choco.ir.memloc<!choco.ir.named_type<"str">>) -> !choco.ir.named_type<"str">
// CHECK-NEXT:     "choco.ir.call_expr"(%21) <{"func_name" = "print"}> : (!choco.ir.named_type<"str">) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
