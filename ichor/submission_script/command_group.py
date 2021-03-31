from ichor.submission_script.command_line import CommandLine
from ichor.common.functools import classproperty
from typing import List, Tuple
from ichor.modules import Modules


class CommandGroup(CommandLine, list):
    @property
    def command(self) -> str:
        return self[0].command

    @property
    def ncores(self) -> int:
        return self[0].ncores

    @property
    def data(self) -> Tuple[str]:
        return self[0].data

    @property
    def modules(self) -> Modules:
        return self[0].modules

    @property
    def arguments(self) -> List[str]:
        return self[0].arguments

    @property
    def options(self) -> List[str]:
        return self[0].options

    def repr(self, variables: List[str]) -> str:
        return self[0].repr(variables)
