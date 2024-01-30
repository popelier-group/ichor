from pathlib import Path

from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file_data import HasAtoms
from ichor.core.files.pandora.morfi_output import MorfiDirectory
from ichor.core.files.pandora.pandora_input import PandoraInput
from ichor.core.files.pandora.pyscf_output import PySCFDirectory


class PandoraDirectory(HasAtoms, AnnotatedDirectory):

    dirname = "pandora"

    contents = {"input": PandoraInput, "pyscf": PySCFDirectory, "morfi": MorfiDirectory}

    def write(self):
        if not self.exists():
            self.mkdir()
        if self.input is None:
            self.input = PandoraInput(
                self.path / (self.path.name + PandoraInput.filetype)
            )
        self.input.atoms = self.atoms
        self.input.write()

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PandoraDirectory.dirname
