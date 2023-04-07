from pathlib import Path

from ichor.core.files.optional_file import OptionalFile
from ichor.hpc import MACHINE
from ichor.hpc.machine import Machine


class CannotFindPandora(Exception):
    pass


def PANDORA_LOCATION() -> Path:
    pandora_location = OptionalFile

    # if GLOBALS.PANDORA_LOCATION != "" and GLOBALS.PANDORA_LOCATION.exists():
    #     if GLOBALS.PANDORA_LOCATION.exists():
    #         if GLOBALS.PANDORA_LOCATION.is_dir():
    #             if (GLOBALS.PANDORA_LOCATION / "pandora.py").exists():
    #                 pandora_location = GLOBALS.PANDORA_LOCATION / "pandora.py"
    #         else:
    #             pandora_location = GLOBALS.PANDORA_LOCATION
    if MACHINE is Machine.ffluxlab:
        pandora_location = Path("/home/modules/apps/pandora/0.1.0/pandora.py")
    elif MACHINE is Machine.csf3:
        pandora_location = Path("/mnt/pp01-home01/shared/pandora/pandora.py")
    else:
        pass
        # implement download for pandora

    if pandora_location is OptionalFile:
        raise CannotFindPandora(
            "Pandora could not be found, please set PANDORA_LOCATION in the config"
        )

    if not pandora_location.exists():
        raise CannotFindPandora(
            f"Cannot find pandora location from: {pandora_location}"
        )

    return pandora_location
