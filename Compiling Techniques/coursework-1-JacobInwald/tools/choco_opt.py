#!/usr/bin/env python3

from typing import IO, List, Type

from xdsl.passes import ModulePass, ModulePassT
from xdsl.xdsl_opt_main import xDSLOptMain

from choco.dialects.choco_ast import ChocoAST
from choco.lexer import Lexer as ChocoLexer
from choco.parser import Parser as ChocoParser


class ChocoOptMain(xDSLOptMain):

    passes_native = list[type[ModulePass]]()

    def register_all_passes(self):
        for pass_ in self.passes_native:
            self.register_pass(pass_)

    def register_all_targets(self):
        super().register_all_targets()

    def pipeline_entry(self, k: str, entries: dict[str, Type[ModulePassT]]):
        """Helper function that returns a pass"""
        if k in entries.keys():
            return entries[k].name

    def setup_pipeline(self):
        self.pipeline = []

    def register_all_dialects(self):
        """Register all dialects that can be used."""
        self.ctx.register_dialect(ChocoAST)

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
    except Exception as e:
        print(str(e))
        exit(0)


if __name__ == "__main__":
    __main__()