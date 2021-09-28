import re
from pathlib import Path

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.wfn import WFN
from ichor.files.optional_file import OptionalFile, OptionalPath


class MorfiWFN(WFN):
    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "morfi.wfn"


class PySCFDirectory(AnnotatedDirectory):
    morfi_wfn: OptionalPath[MorfiWFN] = OptionalFile
    aimall_wfn: OptionalPath[WFN] = OptionalFile

    @classproperty
    def dirname(self) -> str:
        return 'pyscf'

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PySCFDirectory.dirname
