import re
from pathlib import Path
from typing import List

import numpy as np

from ichor.atoms import Atom, Atoms, ListOfAtoms
from ichor.common.io import mkdir
from ichor.files.gjf import GJF
from ichor.files.file import File, FileState


class Trajectory(ListOfAtoms, File):
    """Handles .xyz files that have multiple timesteps, with each timestep giving the x y z coordinates of the
    atoms."""
    def __init__(self, path: Path):
        ListOfAtoms.__init__(self)
        File.__init__(self, path)

    def _read_file(self):
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
                            atom_type, x, y, z = line.split()
                            atoms.add(
                                Atom(atom_type, float(x), float(y), float(z))
                            )
                    self.add(atoms)
                    atoms = Atoms()

    @property
    def filetype(self) -> str:
        return ".xyz"

    def add(self, atoms):
        """Add a list of Atoms (corresponding to one timestep) to the end of the trajectory list"""
        if isinstance(atoms, Atoms):
            self.append(atoms)
        else:
            self.append(Atoms(atoms))

    def extend(self, atoms):
        """extend the current trajectory by another list of atoms (could be another trajectory list)"""
        if isinstance(atoms, Atoms):
            self.extend(atoms)
        else:
            self.extend(Atoms(atoms))

    def write(self, fname=None):
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep."""
        if fname is None:
            fname = self.path
        with open(fname, "w") as f:
            for i, atoms in enumerate(self):
                f.write(f"    {len(atoms)}\ni = {i}\n")
                f.write(f"{atoms}\n")

    def rmsd(self, ref=None):
        if ref is None:
            ref = self[0]
        elif isinstance(ref, int):
            ref = self[ref]

        return [ref.rmsd(point) for point in self]

    def to_set(self, root: Path, indices: List[int]):
        """Converts the geometries in the timesteps to gjf files which then can be passed into Gaussian
        to calculate .wfn files."""
        from ichor.globals import GLOBALS

        mkdir(root, empty=True)
        root = Path(root)
        indices.sort(reverse=True)
        for n, i in enumerate(indices):
            path = Path(
                str(GLOBALS.SYSTEM_NAME) + str(n + 1).zfill(4) + ".gjf"
            )
            gjf = GJF(root / path)
            gjf._atoms = self[i]
            gjf.write()
            del self[i]

    def to_dir(self, root: Path, every: int = 1):
        from ichor.globals import GLOBALS

        for i, geometry in enumerate(self):
            if i % every == 0:
                path = Path(
                    str(GLOBALS.SYSTEM_NAME) + str(i + 1).zfill(4) + ".gjf"
                )
                gjf = GJF(root / path)
                gjf._atoms = geometry
                gjf.write()

    @property
    def features(self) -> np.ndarray:
        """
        Returns:
        :type: `np.ndarray`
        the features for every atom in every timestep. Shape `n_timesteps` x `n_atoms` x `n_features`)
        """
        return np.array([timestep.features for timestep in self])

    def __getitem__(self, item):
        if self.state is not FileState.Read:
            self.read()
        return super().__getitem__(item)

    def __iter__(self):
        if self.state is not FileState.Read:
            self.read()
        return super().__iter__()

    def __len__(self):
        if self.state is not FileState.Read:
            self.read()
        return super().__len__()
