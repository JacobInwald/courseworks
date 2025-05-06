// RUN: choco-opt -p choco-flat-introduce-library-calls %s | filecheck %s

//
// print(True)
//

builtin.module {
  %0 = "choco.ir.literal"() <{"value" = #choco.ir.bool<True>}> : () -> !choco.ir.named_type<"bool">
  "choco.ir.call_expr"(%0) <{"func_name" = "print"}> : (!choco.ir.named_type<"bool">) -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   %0 = "choco.ir.literal"() <{"value" = #choco.ir.bool<True>}> : () -> !choco.ir.named_type<"bool">
// CHECK-NEXT:   "choco.ir.call_expr"(%0) <{"func_name" = "_print_bool"}> : (!choco.ir.named_type<"bool">) -> ()
// CHECK-NEXT: }
