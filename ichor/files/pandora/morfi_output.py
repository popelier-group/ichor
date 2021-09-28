import re
from pathlib import Path

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.mout import MOUT
from ichor.files.optional_file import OptionalPath, OptionalFile


class MorfiDirectory(AnnotatedDirectory):
    mout: OptionalPath[MOUT] = OptionalFile

    @classproperty
    def dirname(self) -> str:
        return 'morfi-2pdm'

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == MorfiDirectory.dirname
