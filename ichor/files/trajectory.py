import re
from pathlib import Path
from typing import List

import numpy as np

from ichor.atoms import Atom, Atoms, ListOfAtoms
from ichor.common.io import mkdir
from ichor.files.file import File, FileState
from ichor.files.gjf import GJF


class Trajectory(ListOfAtoms, File):
    # TODO: get something like trajectory["C1"][2] working, currently it is not
    # TODO: I think Trajectory should return another Trajectory instance when indexed or sliced.
    """Handles .xyz files that have multiple timesteps, with each timestep giving the x y z coordinates of the
    atoms."""

    def __init__(self, path: Path):
        ListOfAtoms.__init__(self)
        File.__init__(self, path)

    def _read_file(self, n: int = -1):
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
                    if n > 0 and len(self) >= n:
                        break
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

    # def extend(self, atoms):
    #     """extend the current trajectory by another list of atoms (could be another trajectory list)"""
    #     if isinstance(atoms, Atoms):
    #         self.extend(atoms)
    #     else:
    #         self.extend(Atoms(atoms))

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
            A 3D array of features for every atom in every timestep. Shape `n_timesteps` x `n_atoms` x `n_features`)
            If the trajectory instance is indexed by str, the array has shape `n_timesteps` x `n_features`.
            If the trajectory instance is indexed by str, the array has shape `n_atoms` x `n_features`.
            If the trajectory instance is indexed by slice, the array has shape `slice`, `n_atoms` x `n_features`.
        """
        return np.array([timestep.features for timestep in self])

    @property
    def coordinates(self) -> np.ndarray:
        """
        Returns:
            :type: `np.ndarray`
            the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        return np.array([timestep.coordinates for timestep in self])

    def __getitem__(self, item):
        # TODO: Implement isinstance(item, slice) if needed
        """ Used to index a Trajectory instance by a str (eg. trajectory['C1']) or by integer (eg. trajectory[2]),
        remember that indeces in Python start at 0, so trajectory[2] is the 3rd timestep.
        You can use something like (np.array([traj[i].features for i in range(2)]).shape) to features of a slice of
        a trajectory as slice is not implemented in __getitem__"""
        if self.state is not FileState.Read:
            self.read()

        return super().__getitem__(item)

    def __iter__(self):
        """ Used to iterate over timesteps (Atoms instances) in places such as for loops"""
        if self.state is not FileState.Read:
            self.read()
        return super().__iter__()

    def __len__(self):
        """ Returns the number of timesteps in the Trajectory instance"""
        if self.state is not FileState.Read:
            self.read()
        return super().__len__()
