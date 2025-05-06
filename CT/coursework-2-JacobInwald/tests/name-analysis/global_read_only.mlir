// RUN: choco-opt -p name-analysis %s | filecheck %s

//
// x: int = 0
// def foo():
//     y: int = 0
//     y = x
//


builtin.module {
  "choco.ast.program"() ({
    "choco.ast.var_def"() ({
      "choco.ast.typed_var"() <{"var_name" = "x"}> ({
        "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
      }) : () -> ()
    }, {
      "choco.ast.literal"() <{"value" = 0 : i32}> : () -> ()
    }) : () -> ()
    "choco.ast.func_def"() <{"func_name" = "foo"}> ({
    ^0:
    }, {
      "choco.ast.type_name"() <{"type_name" = "<None>"}> : () -> ()
    }, {
      "choco.ast.var_def"() ({
        "choco.ast.typed_var"() <{"var_name" = "y"}> ({
          "choco.ast.type_name"() <{"type_name" = "int"}> : () -> ()
        }) : () -> ()
      }, {
        "choco.ast.literal"() <{"value" = 0 : i32}> : () -> ()
      }) : () -> ()
      "choco.ast.assign"() ({
        "choco.ast.id_expr"() <{"id" = "y"}> : () -> ()
      }, {
        "choco.ast.id_expr"() <{"id" = "x"}> : () -> ()
      }) : () -> ()
    }) : () -> ()
  }, {
  ^1:
  }) : () -> ()
}

// CHECK: builtin.module {
