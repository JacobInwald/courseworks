// RUN: choco-opt -p check-assign-target,name-analysis,type-checking %s | filecheck %s

//
// def foo():
//   return foo()
//


builtin.module {
  "choco.ast.program"() ({
    "choco.ast.func_def"() <{"func_name" = "foo"}> ({
    ^0:
    }, {
      "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
    }, {
      "choco.ast.return"() ({
        "choco.ast.call_expr"() <{"func" = "foo"}> ({
        ^1:
        }) : () -> ()
      }) : () -> ()
    }) : () -> ()
  }, {
  ^2:
  }) : () -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   "choco.ast.program"() ({
// CHECK-NEXT:     "choco.ast.func_def"() <{"func_name" = "foo"}> ({
// CHECK-NEXT:     ^0:
// CHECK-NEXT:     }, {
// CHECK-NEXT:       "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
// CHECK-NEXT:     }, {
// CHECK-NEXT:       "choco.ast.return"() ({
// CHECK-NEXT:         "choco.ast.call_expr"() <{"func" = "foo", "type_hint" = !choco.ir.named_type<"<None>">}> ({
// CHECK-NEXT:         ^1:
// CHECK-NEXT:         }) : () -> ()
// CHECK-NEXT:       }) : () -> ()
// CHECK-NEXT:     }) : () -> ()
// CHECK-NEXT:   }, {
// CHECK-NEXT:   ^2:
// CHECK-NEXT:   }) : () -> ()
// CHECK-NEXT: }
