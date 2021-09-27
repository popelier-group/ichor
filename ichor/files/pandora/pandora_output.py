import re
from pathlib import Path

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.morfi_output import MorfiOutput
from ichor.files.pandora.pyscf_output import PySCFOutput


class PandoraOutput(AnnotatedDirectory):
    pyscf: PySCFOutput
    morfi: MorfiOutput

    def __init__(self, path: Path):
        AnnotatedDirectory.__init__(self, path)

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "pyscf"
