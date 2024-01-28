from pathlib import Path

from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.pandora.mout import MOUT


class MorfiDirectory(AnnotatedDirectory):

    contents = {"mout": MOUT}

    # @classproperty
    # def dirname(self) -> str:
    #     return "morfi-2pdm"

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == MorfiDirectory.dirname
