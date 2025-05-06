// RUN: choco-opt -p choco-ast-to-choco-flat %s | filecheck %s

//
// x: int = 0
//

builtin.module {
  "choco.ast.program"() ({
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "x"}> ({
        "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = 0 : i32, "type_hint" = !choco.ir.named_type<"int">}> : () -> ()
    }) : () -> ()
  }, {
  ^0:
  }) : () -> ()
}


// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ir.func_def"() <{"func_name" = "_main", "return_type" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:     %0 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:     %1 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:     "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
