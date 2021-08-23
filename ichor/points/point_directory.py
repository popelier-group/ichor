import os
import re
from typing import Optional

from ichor.atoms import AtomsNotFoundError
from ichor.common.functools import buildermethod, classproperty
from ichor.files import GJF, WFN, Directory, FileState, INTs
from ichor.geometry import AtomData
from ichor.points.point import Point


class PointDirectory(Point, Directory):
    gjf: Optional[GJF] = None
    wfn: Optional[WFN] = None
    ints: Optional[INTs] = None

    def __init__(self, path):
        Directory.__init__(self, path)

    @classproperty
    def dirpattern(self):
        from ichor.globals import GLOBALS

        return re.compile(rf"{GLOBALS.SYSTEM_NAME}\d+")

    # def parse(self):
    #     super().parse()
    # print("setting atoms")
    # if self.ints.path.exists() and self.gjf.path.exists():
    #     print("adding atoms to path")
    #     with self.ints.block():
    #         self.ints.atoms = self.gjf.atoms
    #     print("atoms added")

    @property
    def atoms(self):
        if self.gjf.exists():
            return self.gjf.atoms
        elif self.wfn.exists():
            return self.wfn.atoms
        raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    def get_atom_data(self, atom) -> AtomData:
        if self.ints:
            return AtomData(self.atoms[atom], self.ints[atom])
        else:
            return AtomData(self.atoms[atom])

    def __getattr__(self, item):
        try:
            return getattr(self.ints, item)
        except AttributeError:
            try:
                return getattr(self.gjf, item)
            except AttributeError:
                try:
                    return getattr(self.wfn, item)
                except AttributeError:
                    raise AttributeError(
                        f"'{self.path}' instance of '{self.__class__.__name__}' object has no attribute '{item}'"
                    )

    def __repr__(self):
        return str(self.path)
