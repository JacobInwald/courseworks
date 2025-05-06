// RUN: choco-opt -p check-assign-target,name-analysis,type-checking %s | filecheck %s

//
// pass
//


builtin.module {
  "choco.ast.program"() ({
  ^0:
  }, {
    "choco.ast.pass"() : () -> ()
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ast.program"() ({
// CHECK-NEXT:   ^0:
// CHECK-NEXT:   }, {
// CHECK-NEXT:     "choco.ast.pass"() : () -> ()
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
