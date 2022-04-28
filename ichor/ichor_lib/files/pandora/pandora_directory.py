from pathlib import Path
from typing import Optional

from ichor_lib.common.functools import classproperty
from ichor_lib.files.directory import AnnotatedDirectory
from ichor_lib.files.geometry import GeometryDataFile, GeometryFile
from ichor_lib.files.optional_file import OptionalFile, OptionalPath
from ichor_lib.files.pandora.morfi_output import MorfiDirectory
from ichor_lib.files.pandora.pandora_input import PandoraInput
from ichor_lib.files.pandora.pyscf_output import PySCFDirectory


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
