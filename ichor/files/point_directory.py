import inspect
import re
from pathlib import Path
from typing import Optional

from ichor.atoms import AtomsNotFoundError
from ichor.common.functools import classproperty
from ichor.files.directory import AnnotatedDirectory
from ichor.files.geometry import AtomData, GeometryData, GeometryFile
from ichor.files.gjf import GJF
from ichor.files.ints import INTs
from ichor.files.wfn import WFN
from ichor.files.xyz import XYZ
from ichor.files.pandora import PandoraDirectory


class PointDirectory(GeometryFile, GeometryData, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.

    Attributes:
        cls.gjf Optional[GJF]: Used when iterating over __annotations__
        cls.wfn Optional[WFN]: Used when iterating over __annotations__
        cls.ints Optional[INTs]: Used when iterating over __annotations__
    """

    xyz: Optional[XYZ] = None
    gjf: Optional[GJF] = None
    wfn: Optional[WFN] = None
    ints: Optional[INTs] = None
    pandora: Optional[PandoraDirectory] = None

    def __init__(self, path):
        GeometryFile.__init__(self)
        GeometryData.__init__(self)
        AnnotatedDirectory.__init__(self, path)

    def parse(self):
        super().parse()
        if self.xyz is None:
            for f in self.files():
                if isinstance(f, GeometryFile):
                    self.xyz = XYZ(Path(self.path) / (self.path.name + XYZ.filetype), atoms=f.atoms)
                    self.xyz.write()

    @property
    def atoms(self):
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""
        if self.xyz.exists():
            return self.xyz
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

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_atom_data(item)
        return super().__getitem__(item)
