from pathlib import Path
from typing import Optional

from ichor.atoms import Atom, Atoms
from ichor.common.functools import classproperty
from ichor.files.file import File
from ichor.files.geometry import GeometryFile


class XYZ(GeometryFile, File):
    def __init__(self, path: Path, atoms: Optional[Atoms] = None):
        File.__init__(self, path)

        if atoms is not None:
            self.atoms = atoms
            self.write()

    @classproperty
    def filetype(self) -> str:
        return ".xyz"

    def _read_file(self):
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
        if path is None:
            path = self.path
        with open(path, "w") as f:
            f.write(f"{len(self.atoms)}\n")
            f.write("\n")
            for atom in self.atoms:
                f.write(f"{atom.type} {atom.x} {atom.y} {atom.z}\n")
