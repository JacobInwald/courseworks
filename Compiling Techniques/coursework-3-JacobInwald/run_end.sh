a="temp.s"
choco-opt -p all -t riscv $1 > $a
riscv-interpreter temp.s