#!/usr/bin/env python3

from io import IOBase
from typing import IO, List, Type

from xdsl.dialects.builtin import Builtin, ModuleOp
from xdsl.passes import ModulePass, ModulePassT
from xdsl.utils.parse_pipeline import PipelinePassSpec
from xdsl.xdsl_opt_main import xDSLOptMain

from choco.check_assign_target import CheckAssignTargetPass
from choco.choco_ast_to_choco_flat import ChocoASTToChocoFlat
from choco.choco_flat_introduce_library_calls import ChocoFlatIntroduceLibraryCalls
from choco.choco_flat_to_riscv_ssa import ChocoFlatToRISCVSSA
from choco.constant_folding import ChocoFlatConstantFolding
from choco.dupe_elimination import ChocoFlatDupeElimination
from choco.dead_code_elimination import ChocoFlatDeadCodeElimination
from choco.unused_store import ChocoUnusedStoreElimination
from choco.dialects.choco_ast import ChocoAST
from choco.dialects.choco_flat import ChocoFlat
from choco.for_to_while import ForToWhile
from choco.lexer import Lexer as ChocoLexer
from choco.name_analysis import NameAnalysis
from choco.parser import Parser as ChocoParser
from choco.parser import SyntaxError
from choco.semantic_error import SemanticError
from choco.type_checking import TypeChecking
from choco.warn_dead_code import DeadCodeError, WarnDeadCode
from riscv.dialect import RISCV
from riscv.function_lowering import RISCVFunctionLowering
from riscv.printer import print_program
from riscv.register_allocation import RISCVSSAToRISCV
from riscv.ssa_dialect import RISCVSSA


class ChocoOptMain(xDSLOptMain):
    passes_native: list[type[ModulePass]] = [
        # Semantic Analysis
        CheckAssignTargetPass,
        NameAnalysis,
        TypeChecking,
        WarnDeadCode,
        # IR Generation
        ChocoASTToChocoFlat,
        # IR Optimization
        ChocoFlatIntroduceLibraryCalls,
        # ChocoFlatVarReplacement,
        ChocoFlatDupeElimination,
        ChocoFlatConstantFolding,
        # ChocoUnusedStoreElimination,
        ChocoFlatDupeElimination,
        ChocoFlatDeadCodeElimination,
        ForToWhile,
        # Code Generation
        ChocoFlatToRISCVSSA,
        RISCVSSAToRISCV,
        RISCVFunctionLowering,
    ]

    def register_all_passes(self):
        for pass_ in self.passes_native:
            self.register_pass(pass_)

    def _output_risc(self, prog: ModuleOp, output: IOBase):
        print_program(prog.ops, "riscv", stream=output)  # type: ignore

    def register_all_targets(self):
        super().register_all_targets()
        self.available_targets["riscv"] = lambda prog, output: print_program(
            prog.ops, "riscv", stream=output  # type: ignore
        )

    def pipeline_entry(self, k: str, entries: dict[str, Type[ModulePassT]]):
        """Helper function that returns a pass"""
        if k in entries.keys():
            return entries[k].name

    def setup_pipeline(self):
        entries = {
            "type": TypeChecking,
            "warn": WarnDeadCode,
            "ir": ChocoASTToChocoFlat,
            "fold": ChocoFlatConstantFolding,
            "dead": ChocoFlatDeadCodeElimination,
            "iropt": ForToWhile,
            "riscv": ChocoFlatToRISCVSSA,
        }

        if self.args.passes != "all":
            if self.args.passes in entries:
                pipeline = list(self.available_passes.keys())
                entry = self.pipeline_entry(self.args.passes, entries)
                if entry is None:
                    raise Exception(
                        f"ModulePass corresponding to {self.args.passes} doesn't have a name!"
                    )
                if entry not in ["warn-dead-code"]:
                    # the case where our entry is warn-dead-code only
                    pipeline = list(filter(lambda x: x != "warn-dead-code", pipeline))
                pipeline = [
                    PipelinePassSpec(p, dict())
                    for p in pipeline[: pipeline.index(entry) + 1]
                ]
            else:
                super().setup_pipeline()
                return

        else:
            pipeline = [
                PipelinePassSpec(p, dict())
                for p in self.available_passes
                if p != "warn-dead-code"
            ]

        self.pipeline = [
            self.available_passes[p.name].from_pass_spec(p) for p in pipeline
        ]

    def register_all_dialects(self):
        """Register all dialects that can be used."""
        self.ctx.register_dialect(Builtin)
        self.ctx.register_dialect(RISCV)
        self.ctx.register_dialect(RISCVSSA)
        self.ctx.register_dialect(ChocoAST)
        self.ctx.register_dialect(ChocoFlat)

    def get_passes_as_list(self, native: bool = False) -> List[str]:
        """Add all passes that can be called by choco-opt in a list."""

        pass_list = list[str]()

        if native:
            passes = ChocoOptMain.passes_native
        else:
            passes = ChocoOptMain.passes_native
        for pass_function in passes:
            pass_list.append(pass_function.__name__.replace("_", "-"))

        return pass_list

    def register_all_frontends(self):
        super().register_all_frontends()

        def parse_choco(f: IO[str]):
            lexer = ChocoLexer(f)  # type: ignore
            parser = ChocoParser(lexer)
            program = parser.parse_program()
            return program

        self.available_frontends["choc"] = parse_choco


def __main__():
    choco_main = ChocoOptMain()

    try:
        chunks, file_extension = choco_main.prepare_input()
        output_stream = choco_main.prepare_output()
        for i, chunk in enumerate(chunks):
            try:
                if i > 0:
                    output_stream.write("// -----\n")
                module = choco_main.parse_chunk(chunk, file_extension)
                if module is not None:
                    if choco_main.apply_passes(module):
                        output_stream.write(choco_main.output_resulting_program(module))
                output_stream.flush()
            finally:
                chunk.close()
    except SyntaxError as e:
        print(e.get_message())
        exit(0)
    except SemanticError as e:
        print("Semantic error: %s" % str(e))
        exit(0)
    except DeadCodeError as e:
        print(f"[Warning] Dead code found: {e}")
        exit(0)


if __name__ == "__main__":
    __main__()
