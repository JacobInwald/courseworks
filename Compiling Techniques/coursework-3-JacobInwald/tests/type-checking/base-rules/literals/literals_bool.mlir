// RUN: choco-opt -p check-assign-target,name-analysis,type-checking %s | filecheck %s

//
// True
// False
//


builtin.module {
  "choco.ast.program"() ({
  ^0:
  }, {
    "choco.ast.literal"() <{"value" = #choco.ast.bool<True>}> : () -> ()
    "choco.ast.literal"() <{"value" = #choco.ast.bool<False>}> : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ast.program"() ({
// CHECK-NEXT:   ^0:
// CHECK-NEXT:   }, {
// CHECK-NEXT:     "choco.ast.literal"() <{"value" = #choco.ast.bool<True>, "type_hint" = !choco.ir.named_type<"bool">}> : () -> ()
// CHECK-NEXT:     "choco.ast.literal"() <{"value" = #choco.ast.bool<False>, "type_hint" = !choco.ir.named_type<"bool">}> : () -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
