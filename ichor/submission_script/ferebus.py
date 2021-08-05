from pathlib import Path
from typing import List

from ichor.common.functools import classproperty
from ichor.logging import logger
from ichor.modules import FerebusModules, Modules
from ichor.submission_script.command_line import CommandLine
from ichor.submission_script.ichor import ICHORCommand


class FerebusCommand(CommandLine):
    def __init__(self, ferebus_directory: Path, move_models: bool = True):
        self.ferebus_directory = ferebus_directory
        self.move_models = move_models

    @property
    def data(self) -> List[str]:
        return [str(self.ferebus_directory.absolute())]

    @classproperty
    def modules(self) -> Modules:
        return FerebusModules

    @classproperty
    def command(self) -> str:
        from ichor.globals import GLOBALS

        if not GLOBALS.FEREBUS_LOCATION.is_file():
            logger.warning(
                f"Cannot find FEREBUS location ({GLOBALS.FEREBUS_LOCATION})"
            )
        return str(GLOBALS.FEREBUS_LOCATION.absolute())

    @classproperty
    def ncores(self) -> int:
        from ichor.globals import GLOBALS

        return GLOBALS.FEREBUS_CORE_COUNT

    def repr(self, variables: List[str]) -> str:
        cmd = f"pushd {variables[0]}\n"
        cmd += f"  {self.command}\n"
        cmd += "popd\n"
        if self.move_models:
            move_models = ICHORCommand()
            move_models.run_function("move_models", variables[0])
            cmd += f"{move_models.repr()}\n"
        return cmd
