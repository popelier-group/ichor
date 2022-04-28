import re
from pathlib import Path

from ichor_lib.common.functools import classproperty
from ichor_lib.files.directory import AnnotatedDirectory
from ichor_lib.files.optional_file import OptionalFile, OptionalPath
from ichor_lib.files.wfn import WFN


class MorfiWFN(WFN):
    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "morfi.wfn"


class PySCFDirectory(AnnotatedDirectory):
    morfi_wfn: OptionalPath[MorfiWFN] = OptionalFile
    aimall_wfn: OptionalPath[WFN] = OptionalFile

    @classproperty
    def dirname(self) -> str:
        return "pyscf"

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PySCFDirectory.dirname
