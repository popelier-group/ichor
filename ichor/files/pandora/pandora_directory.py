from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.pandora_input import PandoraInput
from typing import Optional
from ichor.files.pandora.morfi_output import MorfiDirectory
from ichor.files.pandora.pyscf_output import PySCFDirectory
from ichor.common.functools import classproperty
from ichor.files.geometry import GeometryFile, GeometryData

from pathlib import Path


class PandoraDirectory(AnnotatedDirectory, GeometryFile, GeometryData):
    input: Optional[PandoraInput] = None
    pyscf: Optional[PySCFDirectory] = None
    morfi: Optional[MorfiDirectory] = None

    def write(self):
        if not self.exists():
            self.mkdir()
        if self.input is None:
            self.input = PandoraInput(self.path / (self.path.name + PandoraInput.filetype))
        self.input.atoms = self.atoms
        self.input.write()

    @classproperty
    def dirname(self) -> str:
        return 'pandora'

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PandoraDirectory.dirname
