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

def get_wfn_energy_from_file(wfn_file: Path) -> Optional[float]:
    """
    Tries to find the optimum energy for the current system
    :return: ether the optimum energy or None if the optimum energy cannot be found
    :raises: UnknownOptimumEnergyFileType if GLOBALS.OPTIMUM_ENERGY_FILE is provided but is of unknown type
    """

    if wfn_file.exists():
        wfn_energy = WFN(wfn_file).energy
        if wfn_energy is not None:
            return wfn_energy
