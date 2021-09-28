import re
from pathlib import Path

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.wfn import WFN


class MorfiWFN(WFN):
    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "morfi.wfn"


class PySCFDirectory(AnnotatedDirectory):
    morfi_wfn: MorfiWFN
    aimall_wfn: WFN

    @classproperty
    def dirname(self) -> str:
        return 'pyscf'

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PySCFDirectory.dirname
