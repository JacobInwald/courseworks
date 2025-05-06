// RUN: choco-opt -p choco-ast-to-choco-flat %s | filecheck %s

//
// def noresult():
//     return
//
// def noresult2(x: int):
//     return
//
// def result() -> int:
//     return 42
//
// 1
// 1 + 1
//
// noresult()
// noresult2(result())
//

builtin.module {
  "choco.ast.program"() ({
    "choco.ast.func_def"() <{"func_name" = "noresult"}> ({
    ^0:
    }, {
      "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
    }, {
      "choco.ast.return"() ({
      ^1:
      }) : () -> ()
    }) : () -> ()
    "choco.ast.func_def"() <{"func_name" = "noresult2"}> ({
      "choco.ast.typed_var"() <{"var_name" = "x"}> ({
        "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
    }, {
      "choco.ast.return"() ({
      ^2:
      }) : () -> ()
    }) : () -> ()
    "choco.ast.func_def"() <{"func_name" = "result"}> ({
    ^3:
    }, {
      "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
    }, {
      "choco.ast.return"() ({
        "choco.ast.literal"() <{"value" = 42 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
      }) : () -> ()
    }) : () -> ()
  }, {
    "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    "choco.ast.binary_expr"() <{"op" = "+", "type_hint" = !choco.ir.named_type<"int">}> ({
      "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    }) : () -> ()
    "choco.ast.call_expr"() <{"func" = "noresult", "type_hint" = !choco.ir.named_type<"<None>">}> ({
    ^4:
    }) : () -> ()
    "choco.ast.call_expr"() <{"func" = "noresult2", "type_hint" = !choco.ir.named_type<"<None>">}> ({
      "choco.ast.call_expr"() <{"func" = "result", "type_hint" = !choco.ir.named_type<"int">}> ({
      ^5:
      }) : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     "choco.ir.func_def"() <{"func_name" = "noresult", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:       %0 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:       "choco.ir.return"(%0) : (!choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:     "choco.ir.func_def"() <{"func_name" = "noresult2", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     ^0(%1 : !choco.ir.named_type<"int">):
// CHECK-NEXT:       %2 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:       "choco.ir.store"(%2, %1) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:       %3 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:       "choco.ir.return"(%3) : (!choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:     "choco.ir.func_def"() <{"func_name" = "result", "return_type" = !choco.ir.named_type<"int">}> ({
// CHECK-NEXT:       %4 = "choco.ir.literal"() <{"value" = 42 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:       "choco.ir.return"(%4) : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:     %5 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %6 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %7 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %8 = "choco.ir.binary_expr"(%6, %7) <{"op" = "+"}> : (!choco.ir.named_type<"int">, !choco.ir.named_type<"int">) -> !choco.ir.named_type<"int">
// CHECK-NEXT:     "choco.ir.call_expr"() <{"func_name" = "noresult"}> : () -> ()
// CHECK-NEXT:     %9 = "choco.ir.call_expr"() <{"func_name" = "result"}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     "choco.ir.call_expr"(%9) <{"func_name" = "noresult2"}> : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
