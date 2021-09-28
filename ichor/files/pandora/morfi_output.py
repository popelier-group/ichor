import re
from pathlib import Path
from typing import Optional

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.mout import MOUT


class MorfiDirectory(AnnotatedDirectory):
    mout: Optional[MOUT] = None

    @classproperty
    def dirname(self) -> str:
        return 'morfi-2pdm'

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == MorfiDirectory.dirname
