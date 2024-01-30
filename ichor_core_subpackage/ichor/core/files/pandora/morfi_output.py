from pathlib import Path

from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.pandora.mout import MOUT


class MorfiDirectory(AnnotatedDirectory):

    dirname = "morfi-2pdm"
    contents = {"mout": MOUT}

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == MorfiDirectory.dirname
