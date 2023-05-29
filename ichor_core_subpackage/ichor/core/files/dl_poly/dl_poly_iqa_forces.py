from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.files.file import FileContents, ReadFile


class DlPolyIQAForces(ReadFile):
    """READS the IQA_FORCES file from FFLUX.

    :param path: Path to IQA_FORCES file

    :ivar forces: The forces array of shape ntimesteps x natoms x 3.
        Initialized as FileContents prior to file reading.
    :ivar natoms: Number of atoms in each timestep
    """

    def __init__(self, path: Union[Path, str]):

        super().__init__(path)
        self.forces = FileContents
        self.natoms = FileContents

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.stem == "IQA_FORCES"

    def _read_file(self):

        forces = []

        with open(self.path, "r") as f:

            lines = [i.strip().split() for i in f.readlines()]
            # lambda func that maps first argument as int and others as float
            map_func = lambda x: [int(x[0]), *map(float, x[1:])]
            # list of lists. Each inner list has index, cartesian forces
            lines = list(map(map_func, lines))
            max_atom_idx = max(i[0] for i in lines)
            self.natoms = max_atom_idx

            one_timestep_forces = []
            counter = 0

            for line in lines:

                # note that atom index is 1-indexed
                # seems like the ordering of IQA_FORCES is not affected by OpenMP
                cartesian_forces = line[1:]
                one_timestep_forces.append(cartesian_forces)
                counter += 1

                if counter == self.natoms:
                    forces.append(one_timestep_forces)
                    one_timestep_forces = []
                    counter = 0

            # save as array of shape ntimesteps x natoms x 3
            self.forces = np.array(forces)
