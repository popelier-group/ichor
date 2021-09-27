from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.pandora_input import PandoraInput
from typing import Optional
from ichor.files.pandora.morfi_output import MorfiDirectory
from ichor.files.pandora.pyscf_output import PySCFDirectory

from pathlib import Path


class PandoraDirectory(AnnotatedDirectory):
    input: Optional[PandoraInput] = None
    pyscf: Optional[PySCFDirectory] = None
    morfi: Optional[MorfiDirectory] = None

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == 'pandora'
