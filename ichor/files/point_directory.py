from pathlib import Path
from typing import Union

from ichor.atoms import AtomsNotFoundError
from ichor.files.directory import AnnotatedDirectory
from ichor.files.file import FileContents
from ichor.files.geometry import AtomData, GeometryDataFile, GeometryFile
from ichor.files.gjf import GJF
from ichor.files.ints import INTs
from ichor.files.optional_file import OptionalFile, OptionalPath
from ichor.files.pandora import PandoraDirectory, PandoraInput
from ichor.files.wfn import WFN
from ichor.files.xyz import XYZ


class PointDirectory(GeometryFile, GeometryDataFile, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.

    Attributes:
        cls.gjf Optional[GJF]: Used when iterating over __annotations__
        cls.wfn Optional[WFN]: Used when iterating over __annotations__
        cls.ints Optional[INTs]: Used when iterating over __annotations__
    """

    xyz: OptionalPath[XYZ] = OptionalFile
    gjf: OptionalPath[GJF] = OptionalFile
    wfn: OptionalPath[WFN] = OptionalFile
    ints: OptionalPath[INTs] = OptionalFile
    pandora_input: OptionalPath[PandoraInput] = OptionalFile
    pandora: OptionalPath[PandoraDirectory] = OptionalFile

    def __init__(self, path: Union[Path, str]):
        GeometryFile.__init__(self)
        GeometryDataFile.__init__(self)
        AnnotatedDirectory.__init__(self, path)

    def parse(self):
        super().parse()  # call AnnotatedDirectory.parse method
        if not self.xyz:
            for f in self.files():
                if isinstance(f, GeometryFile):
                    self.xyz = XYZ(
                        Path(self.path) / (self.path.name + XYZ.filetype),
                        atoms=f.atoms,
                    )

    @property
    def atoms(self):
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""
        for f in self.files():
            if isinstance(f, GeometryFile):
                return f.atoms
        raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    @atoms.setter
    def atoms(self, value):
        if value is not FileContents:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.filetype}")
            self.xyz = XYZ(self.xyz.path, value)

    def get_atom_data(self, atom) -> AtomData:
        if self.ints.exists():
            return AtomData(self.atoms[atom], self.ints[atom])
        else:
            return AtomData(self.atoms[atom])

    def get_property(self, item: str):
        return getattr(self.ints, item)

    def __getattr__(self, item):
        tried = []
        for d in self.directories():
            try:
                return getattr(d, item)
            except AttributeError:
                tried.append(d.path)
        for f in self.files():
            try:
                return getattr(f, item)
            except AttributeError:
                tried.append(f.path)

        raise AttributeError(
            f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute '{item}', searched: '{tried}'"
        )

    def __repr__(self):
        return str(self.path)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_atom_data(item)
        return super().__getitem__(item)
