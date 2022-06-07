from abc import ABC
from pathlib import Path
from typing import Optional, Union

from ichor.core.files.file import FileContents
from ichor.core.files.geometry import GeometryFile
from ichor.core.atoms import Atoms


class QuantumChemistryProgramInput(GeometryFile, ABC):
    """Abstract class to interface with quantum chemistry programs"""

    def __init__(self, path: Union[Path, str],
                method: Optional[str] = FileContents,
                basis_set: Optional[str] = FileContents,
                atoms: Atoms = FileContents):
        super().__init__(path, atoms)

        self.method = method
        self.basis_set = basis_set
