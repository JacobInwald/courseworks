// RUN: choco-opt -p check-assign-target,name-analysis,type-checking %s | filecheck %s

//
// def foo():
//   pass
//


builtin.module {
  "choco.ast.program"() ({
    "choco.ast.func_def"() <{"func_name" = "foo"}> ({
    ^0:
    }, {
      "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
    }, {
      "choco.ast.pass"() : () -> ()
    }) : () -> ()
  }, {
  ^1:
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ast.program"() ({
// CHECK-NEXT:     "choco.ast.func_def"() <{"func_name" = "foo"}> ({
// CHECK-NEXT:     ^0:
// CHECK-NEXT:     }, {
// CHECK-NEXT:       "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
// CHECK-NEXT:     }, {
// CHECK-NEXT:       "choco.ast.pass"() : () -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:   }, {
// CHECK-NEXT:   ^1:
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
