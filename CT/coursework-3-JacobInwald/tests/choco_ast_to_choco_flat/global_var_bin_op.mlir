// RUN: choco-opt -p type-checking,choco-ast-to-choco-flat %s | filecheck %s

//
// x: int = 1
//
// def f() -> int:
//     global x
//     x = x + 2
//     return 3
//
// # Main program
// print(x + f())
//

builtin.module {
  "choco.ast.program"() ({
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "x"}> ({
        "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    }) : () -> ()
    "choco.ast.func_def"() <{"func_name" = "f"}> ({
    ^0:
    }, {
      "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
    }, {
      "choco.ast.global_decl"() <{"decl_name" = "x"}> : () -> ()
      "choco.ast.assign"() ({
        "choco.ast.id_expr"() <{"id" = "x", "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
      }, {
        "choco.ast.binary_expr"() <{"op" = "+", "type_hint" = !choco.ir.named_type<"int">}> ({
          "choco.ast.id_expr"() <{"id" = "x", "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
        }, {
          "choco.ast.literal"() <{"value" = 2 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
        }) : () -> ()
      }) : () -> ()
      "choco.ast.return"() ({
        "choco.ast.literal"() <{"value" = 3 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
      }) : () -> ()
    }) : () -> ()
  }, {
    "choco.ast.call_expr"() <{"func" = "print", "type_hint" = !choco.ir.named_type<"<None>">}> ({
      "choco.ast.binary_expr"() <{"op" = "+", "type_hint" = !choco.ir.named_type<"int">}> ({
        "choco.ast.id_expr"() <{"id" = "x", "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
      }, {
        "choco.ast.call_expr"() <{"func" = "f", "type_hint" = !choco.ir.named_type<"int">}> ({
        ^1:
        }) : () -> ()
      }) : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %1 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:     "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:     "choco.ir.func_def"() <{"func_name" = "f", "return_type" = !choco.ir.named_type<"int">}> ({
// CHECK-NEXT:       %2 = "choco.ir.load"(%1) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
// CHECK-NEXT:       %3 = "choco.ir.literal"() <{"value" = 2 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:       %4 = "choco.ir.binary_expr"(%2, %3) <{"op" = "+"}> : (!choco.ir.named_type<"int">, !choco.ir.named_type<"int">) -> !choco.ir.named_type<"int">
// CHECK-NEXT:       "choco.ir.store"(%1, %4) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:       %5 = "choco.ir.literal"() <{"value" = 3 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:       "choco.ir.return"(%5) : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:     %6 = "choco.ir.load"(%1) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %7 = "choco.ir.call_expr"() <{"func_name" = "f"}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %8 = "choco.ir.binary_expr"(%6, %7) <{"op" = "+"}> : (!choco.ir.named_type<"int">, !choco.ir.named_type<"int">) -> !choco.ir.named_type<"int">
// CHECK-NEXT:     "choco.ir.call_expr"(%8) <{"func_name" = "print"}> : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
