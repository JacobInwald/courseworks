// RUN: choco-opt %s | filecheck %s

//
// print(input())
//

builtin.module {
  %0 = "choco.ir.call_expr"() <{"func_name" = "input"}> : () -> !choco.ir.named_type<"int">
  "choco.ir.call_expr"(%0) <{"func_name" = "print"}> : (!choco.ir.named_type<"int">) -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   %0 = "choco.ir.call_expr"() <{"func_name" = "input"}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:   "choco.ir.call_expr"(%0) <{"func_name" = "print"}> : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT: }
