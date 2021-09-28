import json
from enum import Enum
from pathlib import Path
from typing import Optional

from ichor.atoms import Atom, Atoms
from ichor.common.functools import classproperty
from ichor.files.qcp import QuantumChemistryProgramInput
from ichor.globals import GLOBALS


class PandoraCCSDmod(Enum):
    CCSD = "ccsd"
    CCSD_HF = "ccsdHF"


class PandoraInput(QuantumChemistryProgramInput):
    def __init__(self, path: Path):
        QuantumChemistryProgramInput.__init__(self, path)

        self.ccsdmod: Optional[PandoraCCSDmod] = None

        self.morfi_grid_radial: Optional[float] = None
        self.morfi_grid_angular: Optional[int] = None

    @classproperty
    def filetype(self) -> str:
        return ".pandora"

    def _read_file(self):
        with open(self.path, "r") as f:
            data = json.load(f)
        self.atoms = Atoms()
        for atom in data["system"]["geometry"]:
            self.atoms.add(Atom(atom[0], atom[1], atom[2], atom[3]))
        self.ccsdmod = PandoraCCSDmod(data["pandora"]["ccsdmod"])
        self.basis_set = data["pyscf"]["method"]
        self.basis_set = data["pyscf"]["basis_set"]
        self.morfi_grid_angular = data["morfi"]["grid"]["angular"]
        self.morfi_grid_radial = data["morfi"]["grid"]["radial"]

    def format(self):
        self.method = GLOBALS.METHOD.lower()
        self.basis_set = GLOBALS.BASIS_SET.lower()
        if not self.basis_set.startswith("unc-"):
            self.basis_set = "unc-" + self.basis_set
        self.ccsdmod = PandoraCCSDmod(GLOBALS.PANDORA_CCSDMOD)
        self.morfi_grid_angular = GLOBALS.MORFI_ANGULAR
        self.morfi_grid_radial = GLOBALS.MORFI_RADIAL

    def write(self):
        self.format()
        data = {
            "system": {
                "name": GLOBALS.SYSTEM_NAME.lower(),
                "geometry": [
                    [atom.type, atom.x, atom.y, atom.z] for atom in self.atoms
                ],
            },
            "pandora": {
                "ccsdmod": self.ccsdmod.value,
            },
            "pyscf": {
                "method": self.method,
                "basis_set": self.basis_set,
            },
            "morfi": {
                "grid": {
                    "radial": self.morfi_grid_radial,
                    "angular": self.morfi_grid_angular,
                },
            },
        }

        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)
