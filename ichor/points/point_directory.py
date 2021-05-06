import os
import re
from typing import Optional

from ichor.common.functools import classproperty
from ichor.files import GJF, WFN, Directory, INTs
from ichor.points.point import Point


class PointDirectory(Point, Directory):
    gjf: Optional[GJF]
    wfn: Optional[WFN]
    ints: Optional[INTs]

    def __init__(self, path):
        Directory.__init__(self, path)

    @classproperty
    def dirpattern(self) -> re.Pattern:
        from ichor.globals import GLOBALS

        return re.compile(rf"{GLOBALS.SYSTEM_NAME}\d+")

    def __getattr__(self, item):
        if item in self.__dict__.keys():
            return self.__dict__[item]
        try:
            return getattr(self.ints, item)
        except AttributeError:
            # raise AttributeError(f"'{self.__class__}' object has no attribute '{item}'")
            try:
                return getattr(self.wfn, item)
            except AttributeError:
                raise AttributeError(
                    f"'{self.__class__}' object has no attribute '{item}'"
                )

    def __repr__(self):
        return str(self.path)
