from pathlib import Path
from typing import Optional

from ichor.core.common.functools import classproperty
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.geometry import GeometryDataFile, GeometryFile
from ichor.core.files.optional_file import OptionalFile, OptionalPath
from ichor.core.files.pandora.morfi_output import MorfiDirectory
from ichor.core.files.pandora.pandora_input import PandoraInput
from ichor.core.files.pandora.pyscf_output import PySCFDirectory


class PandoraDirectory(AnnotatedDirectory, GeometryFile, GeometryDataFile):
    pyscf: OptionalPath[PySCFDirectory] = OptionalFile
    morfi: OptionalPath[MorfiDirectory] = OptionalFile

    def write(self):
        if not self.exists():
            self.mkdir()
        if self.input is None:
            self.input = PandoraInput(
                self.path / (self.path.name + PandoraInput.filetype)
            )
        self.input.atoms = self.atoms
        self.input.write()

    @classproperty
    def dirname(self) -> str:
        return "pandora"

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PandoraDirectory.dirname
