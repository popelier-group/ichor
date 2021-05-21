from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.modules import Modules, PythonModules
from ichor.submission_script.command_line import CommandLine


class PythonCommand(CommandLine):
    def __init__(self, python_script: Path, args: Optional[List[str]] = None):
        self.script = python_script
        self.args = args if args is not None else []

    @classproperty
    def modules(self) -> Modules:
        return PythonModules

    @classproperty
    def command(self) -> str:
        return "python"

    def repr(self, variables=None) -> str:
        return f"{self.command} {self.script} {' '.join(self.args)}"
