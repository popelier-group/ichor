from pathlib import Path

from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.gaussian import WFN


class MorfiWFN(WFN):
    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "morfi.wfn"


class PySCFDirectory(AnnotatedDirectory):

    dirname = "pyscf"
    contents = {"morfi_wfn": MorfiWFN, "aimall_wfn": WFN}

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == PySCFDirectory.dirname
