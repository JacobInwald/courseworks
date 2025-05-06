// RUN: choco-opt -p choco-flat-introduce-library-calls %s | filecheck %s

//
// print(1)
//

builtin.module {
  %0 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
  "choco.ir.call_expr"(%0) <{"func_name" = "print"}> : (!choco.ir.named_type<"int">) -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   %0 = "choco.ir.literal"() <{"value" = 1 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:   "choco.ir.call_expr"(%0) <{"func_name" = "_print_int"}> : (!choco.ir.named_type<"int">) -> ()
// CHECK-NEXT: }
