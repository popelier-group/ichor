import json
from enum import Enum
from pathlib import Path
from typing import Optional

from ichor.atoms import Atom, Atoms
from ichor.common.functools import classproperty
from ichor.files.file import FileContents
from ichor.files.qcp import QuantumChemistryProgramInput

class PandoraCCSDmod(Enum):
    CCSD = "ccsd"
    CCSD_HF = "ccsdHF"
    CCSD_MULLER = "ccsdM"


class PandoraInput(QuantumChemistryProgramInput):
    def __init__(self, path: Path,
        ccsdmod: PandoraCCSDmod = FileContents,
        morfi_grid_radial: float = FileContents,
        morfi_grid_angular: int = FileContents,
        morfi_grid_radial_h: float = FileContents,
        morfi_grid_angular_h: int = FileContents,
        method: str = FileContents,
        basis_set: str = FileContents
    ):
        QuantumChemistryProgramInput.__init__(self, path)

        self.ccsdmod: PandoraCCSDmod = ccsdmod
        self.morfi_grid_radial: float = morfi_grid_radial
        self.morfi_grid_angular: int = morfi_grid_angular
        self.morfi_grid_radial_h: float = morfi_grid_radial_h
        self.morfi_grid_angular_h: int = morfi_grid_angular_h
        self.method = method
        self.basis_set = basis_set

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
        self.basis_set = data["pyscf"]["basis"]
        self.morfi_grid_angular = data["morfi"]["grid"]["angular"]
        self.morfi_grid_radial = data["morfi"]["grid"]["radial"]
        self.morfi_grid_angular_h = data["morfi"]["grid"]["angular_h"]
        self.morfi_grid_radial_h = data["morfi"]["grid"]["radial_h"]

    def format(self):
        self.atoms.centre()
        # todo: ensure no atoms are at the origin (wihtin 1e-6) as this will break morfi

        if not self.basis_set.startswith("unc-"):
            self.basis_set = "unc-" + self.basis_set

    def write(self, system_name: str):
        self.format()
        data = {
            "system": {
                "name": system_name.lower(),
                "geometry": [
                    [atom.type, atom.x, atom.y, atom.z] for atom in self.atoms
                ],
            },
            "pandora": {
                "ccsdmod": self.ccsdmod.value,
            },
            "pyscf": {
                "method": self.method,
                "basis": self.basis_set,
            },
            "morfi": {
                "grid": {
                    "radial": self.morfi_grid_radial,
                    "angular": self.morfi_grid_angular,
                    "radial_h": self.morfi_grid_radial_h,
                    "angular_h": self.morfi_grid_angular_h,
                },
            },
        }

        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)
