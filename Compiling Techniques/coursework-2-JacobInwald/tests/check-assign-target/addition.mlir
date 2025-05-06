// RUN: choco-opt -p check-assign-target %s | filecheck %s

//
// 1 = 1 + 1
//

builtin.module {
  "choco.ast.program"() ({
  ^0:
  }, {
    "choco.ast.assign"() ({
      "choco.ast.literal"() <{"value" = 1 : i32}> : () -> ()
    }, {
      "choco.ast.binary_expr"() <{"op" = "+"}> ({
        "choco.ast.literal"() <{"value" = 1 : i32}> : () -> ()
      }, {
        "choco.ast.literal"() <{"value" = 1 : i32}> : () -> ()
      }) : () -> ()
    }) : () -> ()
  }) : () -> ()
}

// CHECK: Semantic error: Found Literal as the left-hand side of an assignment. Expected to find variable name or index expression only.
