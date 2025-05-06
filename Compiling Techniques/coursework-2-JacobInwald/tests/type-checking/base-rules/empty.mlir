// RUN: choco-opt -p check-assign-target,name-analysis,type-checking %s | filecheck %s

//
//
//


builtin.module {
  "choco.ast.program"() ({
  ^0:
  }, {
  ^1:
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ast.program"() ({
// CHECK-NEXT:   ^0:
// CHECK-NEXT:   }, {
// CHECK-NEXT:   ^1:
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
