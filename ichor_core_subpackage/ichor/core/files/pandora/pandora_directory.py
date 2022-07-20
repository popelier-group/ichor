from pathlib import Path
from typing import Optional, Union, Dict

from ichor.core.common.functools import classproperty
from ichor.core.files.directory import AnnotatedDirectory

from ichor.core.atoms import Atoms
from ichor.core.files.file_data import HasAtoms, HasProperties
from ichor.core.files.optional_file import OptionalFile, OptionalPath
from ichor.core.files.pandora.morfi_output import MorfiDirectory
from ichor.core.files.pandora.pandora_input import PandoraInput
from ichor.core.files.pandora.pyscf_output import PySCFDirectory


class PandoraDirectory(HasAtoms, HasProperties, AnnotatedDirectory):
    input: OptionalPath[PandoraInput] = OptionalFile
    pyscf: OptionalPath[PySCFDirectory] = OptionalFile
    morfi: OptionalPath[MorfiDirectory] = OptionalFile

    def __init__(self, path: Union[str, Path], atoms: Optional[Atoms] = None):
        AnnotatedDirectory.__init__(self, path)
        HasAtoms.__init__(self, atoms)

    def write(self):
        if not self.exists():
            self.mkdir()
        if self.input is None:
            self.input = PandoraInput(
                self.path / (self.path.name + PandoraInput.filetype)
            )
        self.input.atoms = self.atoms
        self.input.write()
    
    @property
    def properties(self) -> Dict[str, float]:
        return self.morfi.properties

    @classproperty
    def dirname(self) -> str:
        return "pandora"

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PandoraDirectory.dirname
