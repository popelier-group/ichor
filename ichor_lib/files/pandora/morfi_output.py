import re
from pathlib import Path

from ichor_lib.common.functools import classproperty
from ichor_lib.files.directory import AnnotatedDirectory
from ichor_lib.files.optional_file import OptionalFile, OptionalPath
from ichor_lib.files.pandora.mout import MOUT


class MorfiDirectory(AnnotatedDirectory):
    mout: OptionalPath[MOUT] = OptionalFile

    @classproperty
    def dirname(self) -> str:
        return "morfi-2pdm"

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == MorfiDirectory.dirname
