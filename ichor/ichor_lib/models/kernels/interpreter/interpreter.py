from typing import Dict

from ichor.models.kernels import Kernel
from ichor.models.kernels.interpreter.parser import Parser


class KernelInterpreter:
    def __init__(self, text: str, global_state: Dict[str, Kernel]):
        self.parser = Parser(text)
        self.global_state = global_state

    def interpret(self) -> Kernel:
        tree = self.parser.parse()
        return tree.visit(self.global_state)
