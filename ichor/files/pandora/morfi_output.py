import re
from pathlib import Path
from typing import Optional

from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.pandora.mout import MOUT


class MorfiDirectory(AnnotatedDirectory):
    mout: Optional[MOUT] = None

    def __init__(self, path: Path):
        AnnotatedDirectory.__init__(self, path)

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name == "morfi-2pdm"
