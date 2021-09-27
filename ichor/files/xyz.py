from ichor.atoms import Atoms, Atom
from ichor.files.file import File
from ichor.common.functools import classproperty
from pathlib import Path
from typing import Optional


class XYZ(Atoms, File):
    def __init__(self, path: Path, atoms=None):
        Atoms.__init__(self, atoms=atoms)
        File.__init__(self, path)

    @classproperty
    def filetype(self) -> str:
        return '.xyz'

    def _read_file(self):
        with open(self.path, 'r') as f:
            natoms = int(next(f))
            _ = next(f)  # blank line
            for _ in range(natoms):
                record = next(f).split()
                self.add(Atom(record[0], float(record[1]), float(record[2]), float(record[3])))

    def write(self, path: Optional[Path] = None):
        if path is None:
            path = self.path
        with open(path, 'w') as f:
            f.write(f'{len(self)}\n')
            f.write('\n')
            for atom in self:
                f.write(f'{atom.type} {atom.x} {atom.y} {atom.z}')
