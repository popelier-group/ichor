from pathlib import Path
from typing import Optional

from ichor.ichor_lib.common.io import get_files_of_type
from ichor.ichor_lib.files import WFN

class UnknownOptimumEnergyFileType(Exception):
    pass


def get_wfn_energy_from_dir(d: Path) -> Optional[float]:
    wfns = get_files_of_type(WFN.filetype, d)
    if len(wfns) > 0:
        return WFN(wfns[0]).energy
    return None


def find_opt() -> Optional[float]:
    """
    Tries to find the optimum energy for the current system
    :return: ether the optimum energy or None if the optimum energy cannot be found
    :raises: UnknownOptimumEnergyFileType if GLOBALS.OPTIMUM_ENERGY_FILE is provided but is of unknown type
    """
    if GLOBALS.OPTIMUM_ENERGY is not None:
        return GLOBALS.OPTIMUM_ENERGY
    if (
        GLOBALS.OPTIMUM_ENERGY_FILE is not None
        and GLOBALS.OPTIMUM_ENERGY_FILE.exists()
    ):
        if GLOBALS.OPTIMUM_ENERGY_FILE.is_dir():
            if (
                GLOBALS.OPTIMUM_ENERGY_FILE / FILE_STRUCTURE["opt"]
            ).exists():  # ichor directory
                wfn_energy = get_wfn_energy_from_dir(
                    GLOBALS.OPTIMUM_ENERGY_FILE / FILE_STRUCTURE["opt"]
                )
                if wfn_energy is not None:
                    return wfn_energy
            wfn_energy = get_wfn_energy_from_dir(
                GLOBALS.OPTIMUM_ENERGY_FILE
            )  # search directory for wfn
            if wfn_energy is not None:
                return wfn_energy
        elif (
            GLOBALS.OPTIMUM_ENERGY_FILE.is_file()
            and GLOBALS.OPTIMUM_ENERGY_FILE.suffix == WFN.filetype
        ):
            return WFN(GLOBALS.OPTIMUM_ENERGY_FILE).energy
        raise UnknownOptimumEnergyFileType(
            f"Unknown filetype for optimum energy file {GLOBALS.OPTIMUM_ENERGY_FILE}, must be of type {WFN.filetype}"
        )
    if FILE_STRUCTURE["opt"].exists():
        wfn_energy = get_wfn_energy_from_dir(FILE_STRUCTURE["opt"])
        if wfn_energy is not None:
            return wfn_energy
    return None
