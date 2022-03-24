from abc import ABC
from pathlib import Path
from typing import Optional, Union

from ichor.files.file import File, FileContents
from ichor.files.geometry import GeometryFile


class QuantumChemistryProgramInput(GeometryFile, ABC):
    """Abstract class to interface with quantum chemistry programs"""

    def __init__(self, path: Union[Path, str]):
        super().__init__(path)

        self.method: Optional[str] = FileContents
        self.basis_set: Optional[str] = FileContents
