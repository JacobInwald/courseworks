// RUN: choco-opt %s | filecheck %s

builtin.module {
  %0 = "riscv_ssa.li"() <{"immediate" = 42 : i64}> : () -> !riscv_ssa.reg
  %1 = "riscv_ssa.mul"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %2 = "riscv_ssa.mulh"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %3 = "riscv_ssa.mulhsu"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %4 = "riscv_ssa.mulhu"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %5 = "riscv_ssa.div"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %6 = "riscv_ssa.divu"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %7 = "riscv_ssa.rem"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
  %8 = "riscv_ssa.remu"(%0, %0): (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
}

// CHECK:       builtin.module {
// CHECK-NEXT:    %0 = "riscv_ssa.li"() <{"immediate" = 42 : i64}> : () -> !riscv_ssa.reg
// CHECK-NEXT:    %1 = "riscv_ssa.mul"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %2 = "riscv_ssa.mulh"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %3 = "riscv_ssa.mulhsu"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %4 = "riscv_ssa.mulhu"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %5 = "riscv_ssa.div"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %6 = "riscv_ssa.divu"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %7 = "riscv_ssa.rem"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:    %8 = "riscv_ssa.remu"(%0, %0) : (!riscv_ssa.reg, !riscv_ssa.reg) -> !riscv_ssa.reg
// CHECK-NEXT:  }
