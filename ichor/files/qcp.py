from abc import ABC
from pathlib import Path
from typing import Optional

from ichor.files.file import File
from ichor.files.geometry import GeometryFile


class QuantumChemistryProgramInput(GeometryFile, File, ABC):
    """Abstract class to interface with quantum chemistry programs"""

    def __init__(self, path: Path):
        File.__init__(self, path)
        GeometryFile.__init__(self)

        self.method: Optional[str] = None
        self.basis_set: Optional[str] = None
