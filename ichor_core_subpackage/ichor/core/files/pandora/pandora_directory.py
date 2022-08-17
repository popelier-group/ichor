from pathlib import Path

from ichor.core.common.functools import classproperty
from ichor.core.files.directory import AnnotatedDirectory

from ichor.core.files import HasAtoms
from ichor.core.files import OptionalFile, OptionalPath
from ichor.core.files import MorfiDirectory
from ichor.core.files import PandoraInput
from ichor.core.files import PySCFDirectory

class PandoraDirectory(HasAtoms, AnnotatedDirectory):
    input: OptionalPath[PandoraInput] = OptionalFile
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
