// RUN: choco-opt %s | filecheck %s

// This test checks if the verifiers work as expected

//
// x: int = 0
// l: [int] = None
// y: int = 0
// x
// l[y] = y
//

builtin.module {
    %0 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
    %1 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
    "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
    %2 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
    %3 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>
    "choco.ir.store"(%3, %2) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>, !choco.ir.named_type<"<None>">) -> ()
    %4 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
    %5 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
    "choco.ir.store"(%5, %4) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
    %6 = "choco.ir.load"(%5) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
    %7 = "choco.ir.load"(%3) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>) -> !choco.ir.list_type<!choco.ir.named_type<"int">>
    %8 = "choco.ir.load"(%5) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
    %9 = "choco.ir.get_address"(%7, %8) : (!choco.ir.list_type<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> !choco.ir.memloc<!choco.ir.named_type<"int">>
    "choco.ir.store"(%9, %6) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
}

// CHECK:      builtin.module {
// CHECK-NEXT:   %0 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:   %1 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:   "choco.ir.store"(%1, %0) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   %2 = "choco.ir.literal"() <{"value" = #choco.ir.none}> : () -> !choco.ir.named_type<"<None>">
// CHECK-NEXT:   %3 = "choco.ir.alloc"() <{"type" = !choco.ir.list_type<!choco.ir.named_type<"int">>}> : () -> !choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>
// CHECK-NEXT:   "choco.ir.store"(%3, %2) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>, !choco.ir.named_type<"<None>">) -> ()
// CHECK-NEXT:   %4 = "choco.ir.literal"() <{"value" = 0 : i32}> : () -> !choco.ir.named_type<"int">
// CHECK-NEXT:   %5 = "choco.ir.alloc"() <{"type" = !choco.ir.named_type<"int">}> : () -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:   "choco.ir.store"(%5, %4) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT:   %6 = "choco.ir.load"(%5) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
// CHECK-NEXT:   %7 = "choco.ir.load"(%3) : (!choco.ir.memloc<!choco.ir.list_type<!choco.ir.named_type<"int">>>) -> !choco.ir.list_type<!choco.ir.named_type<"int">>
// CHECK-NEXT:   %8 = "choco.ir.load"(%5) : (!choco.ir.memloc<!choco.ir.named_type<"int">>) -> !choco.ir.named_type<"int">
// CHECK-NEXT:   %9 = "choco.ir.get_address"(%7, %8) : (!choco.ir.list_type<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> !choco.ir.memloc<!choco.ir.named_type<"int">>
// CHECK-NEXT:   "choco.ir.store"(%9, %6) : (!choco.ir.memloc<!choco.ir.named_type<"int">>, !choco.ir.named_type<"int">) -> ()
// CHECK-NEXT: }
