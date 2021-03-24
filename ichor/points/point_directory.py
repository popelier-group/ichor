from ichor.points.point import Point
from ichor.files import Directory, GJF, WFN, INTs
from typing import Optional
import re
import os
from ichor.globals import GLOBALS
from ichor.common.functools import classproperty


class PointDirectory(Point, Directory):
    gjf: Optional[GJF]
    wfn: Optional[WFN]
    ints: Optional[INTs]

    def __init__(self, path):
        Directory.__init__(self, path)

    @classproperty
    def dirpattern(self) -> re.Pattern:
        return re.compile(rf"{GLOBALS.SYSTEM_NAME}\d+")

    def __getattr__(self, item):
        if item in self.__dict__.keys():
            return self.__dict__[item]
        try:
            return getattr(self.ints, item)
        except AttributeError:
            raise AttributeError(f"'{self.__class__}' object has no attribute '{item}'")

    def __repr__(self):
        return str(self.path)
