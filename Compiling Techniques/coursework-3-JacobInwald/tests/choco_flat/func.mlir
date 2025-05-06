// RUN: choco-opt %s | filecheck %s

//
// def foo():
//    5
//

builtin.module {
  "choco.ir.func_def"() <{"func_name" = "foo", "return_type" = !choco.ir.named_type<"<None>">}> ({
    %0 = "choco.ir.literal"() <{"value" = 5 : i32}> : () -> !choco.ir.named_type<"int">
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "foo", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = 5 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
