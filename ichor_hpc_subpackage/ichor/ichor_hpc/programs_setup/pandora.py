from pathlib import Path

from ichor.ichor_lib.files import OptionalFile
from ichor.ichor_hpc import GLOBALS
from ichor.ichor_hpc import MACHINE, Machine


class CannotFindPandora(Exception):
    pass


def PANDORA_LOCATION() -> Path:
    pandora_location = OptionalFile

    if GLOBALS.PANDORA_LOCATION != "" and GLOBALS.PANDORA_LOCATION.exists():
        if GLOBALS.PANDORA_LOCATION.exists():
            if GLOBALS.PANDORA_LOCATION.is_dir():
                if (GLOBALS.PANDORA_LOCATION / "pandora.py").exists():
                    pandora_location = GLOBALS.PANDORA_LOCATION / "pandora.py"
            else:
                pandora_location = GLOBALS.PANDORA_LOCATION
    elif MACHINE is Machine.ffluxlab:
        pandora_location = Path("/home/modules/apps/pandora/0.1.0/pandora.py")
    elif MACHINE is Machine.csf3:
        pandora_location = Path("/mnt/pp01-home01/shared/pandora/pandora.py")
    else:
        pass
        # implement download for pandora

    if pandora_location is OptionalFile:
        raise CannotFindPandora(
            f"Pandora could not be found, please set PANDORA_LOCATION in the config"
        )

    if not pandora_location.exists():
        raise CannotFindPandora(
            f"Cannot find pandora location from: {pandora_location}"
        )

    return pandora_location
