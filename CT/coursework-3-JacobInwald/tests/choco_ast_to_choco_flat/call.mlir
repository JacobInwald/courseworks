// RUN: choco-opt -p choco-ast-to-choco-flat %s | filecheck %s

//
// print(1)
//

builtin.module {
  "choco.ast.program"() ({
  ^0:
  }, {
    "choco.ast.call_expr"() <{"func" = "print", "type_hint" = !choco.ir.named_type<"<None>">}> ({
      "choco.ast.literal"() <{"value" = 1 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     "choco.ir.call_expr"(%0) <{"func_name" = "print"}> : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
