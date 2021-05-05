from pathlib import Path
from ichor.common.functools import buildermethod
from ichor.atoms.atoms import Atoms
import re
from ichor.globals import GLOBALS
from ichor.files import GJF
import numpy as np


class Trajectory(list):
    def __init__(self, path):
        self.path = Path(path)

        self.read()

    @buildermethod
    def read(self, n=-1):
        with open(self.path, "r") as f:
            atoms = Atoms()
            for line in f:
                if not line.strip():
                    continue
                elif re.match(r"^\s*\d+$", line):
                    natoms = int(line)
                    while len(atoms) < natoms:
                        line = next(f)
                        if re.match(
                            r"\s*\w+(\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?){3}", line
                        ):
                            atoms.add(line)
                    atoms.finish()
                    self.add(atoms)
                    if n > 0 and len(self) > n:
                        break
                    atoms = Atoms()

    def add(self, atoms):
        """ Add a list of Atoms (corresponding to one timestep) to the end of the trajectory list"""

        if isinstance(atoms, Atoms):
            self.append(atoms)
        else:
            self.append(Atoms(atoms))

    def extend(self, atoms):
        """ extend the current trajectory by another list of atoms (could be another trajectory list)"""

        if isinstance(atoms, Atoms):
            self.extend(atoms)
        else:
            self.extend(Atoms(atoms))

    def write(self, fname=None):
        if fname is None:
            fname = self.fname
        with open(fname, "w") as f:
            for i, atoms in enumerate(self):
                f.write(f"    {len(atoms)}\ni = {i}\n")
                f.write(f"{atoms}\n")

    def rmsd(self, ref=None):
        if ref is None:
            ref = self[0]
        elif isinstance(ref, int):
            ref = self[ref]

        rmsd = []
        for point in self:
            rmsd += [ref.rmsd(point)]
        return rmsd

    def to_set(self, root, indices):
        FileTools.mkdir(root, empty=True)
        root = Path(root)
        indices.sort(reverse=True)
        for n, i in enumerate(indices):
            path = Path(
                str(GLOBALS.SYSTEM_NAME) + str(n + 1).zfill(4) + ".gjf"
            )
            gjf = GJF(root / path)
            gjf._atoms = self[i]
            gjf.write()
            del self._trajectory[i]

    def to_dir(self, root, every=1):
        root = Path(root)
        for i, geometry in enumerate(self):
            if i % every == 0:
                path = Path(
                    str(GLOBALS.SYSTEM_NAME) + str(i + 1).zfill(4) + ".gjf"
                )
                gjf = GJF(root / path)
                gjf._atoms = geometry
                gjf.write()

    @property
    def features(self):
        return np.array([atoms.features for atoms in self])

    def __len__(self):
        return len(self._trajectory)

    def __getitem__(self, i):
        return self._trajectory[i]
