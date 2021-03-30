from pathlib import Path
from typing import Tuple

from ichor.common.functools import classproperty
from ichor.globals import GLOBALS
from ichor.logging import logger
from ichor.submission_script.command_line import CommandLine


class FerebusCommand(CommandLine):
    def __init__(self, ferebus_directory: Path):
        self.ferebus_directory = ferebus_directory

    @classproperty
    def data(self) -> Tuple[str]:
        return (str(self.ferebus_directory.absolute),)

    @classproperty
    def command(self) -> str:
        if not GLOBALS.FEREBUS_LOCATION.is_file():
            logger.warning(
                f"Cannot find FEREBUS location ({GLOBALS.FEREBUS_LOCATION})"
            )
        return str(GLOBALS.FEREBUS_LOCATION.absolute())

    @classproperty
    def ncores(self) -> int:
        return GLOBALS.FEREBUS_CORE_COUNT

    def repr(self) -> str:
        cmd = f"pushd {self.batch_index(0)}\n"
        cmd += f"  {self.command}\n"
        cmd += "popd\n"
        return cmd
