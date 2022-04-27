from pathlib import Path
from typing import Optional, Union

from ichor.atoms import Atom, Atoms
from ichor.common.functools import classproperty
from ichor.files.file import File, FileContents
from ichor.files.geometry import GeometryFile


class XYZ(GeometryFile):
    """A class which wraps around a .xyz file that is contained in each PointDirectory. This .xyz file should always be there and it is
    used to write out .gjf files. Each instance of `XYZ` only has one geometry. If there is a need to
    read a `.xyz` file that contains multiple geometries (i.e. a trajectory file), the use the `Trajectory`
    class.

    :param path: The path to an .xyz file
    :param atoms: Optional list of Atoms which can be used to construct a .xyz file. If a list of atoms is passed, then a new xyz file
        with the given Atoms will be written to the given Path.
    """

    def __init__(self, path: Union[Path, str], atoms: Optional[Atoms] = None):
        super().__init__(path)

        self.atoms = FileContents
        if atoms is not None:
            self.atoms = atoms
            self.write()

    @classproperty
    def filetype(self) -> str:
        return ".xyz"

    def _read_file(self):
        """Read a .xyz file and constructs the `self.atoms` attribute which is an instance of `Atoms`"""
        with open(self.path, "r") as f:
            natoms = int(next(f))
            _ = next(f)  # blank line
            self.atoms = Atoms()
            for _ in range(natoms):
                record = next(f).split()
                self.atoms.add(
                    Atom(
                        record[0],
                        float(record[1]),
                        float(record[2]),
                        float(record[3]),
                    )
                )

    def write(self, path: Optional[Path] = None):
        """Write a .xyz to a given path. If no path is given, it will write it to the path given when the XYZ instance was constructed.

        :param path: An optional path to which to write the .xyz file
        """
        if path is None:
            path = self.path
        with open(path, "w") as f:
            f.write(f"{len(self.atoms)}\n")
            f.write("\n")
            for atom in self.atoms:
                f.write(f"{atom.type} {atom.x} {atom.y} {atom.z}\n")
