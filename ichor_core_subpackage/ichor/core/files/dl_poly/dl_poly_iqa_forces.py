from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.files.file import FileContents, ReadFile


class DlPolyIQAForces(ReadFile):
    """READS the IQA_FORCES file from FFLUX.

    :param path: Path to IQA_FORCES file
    :param natoms: Number of atoms in the system.

    :ivar forces: The forces array of shape ntimesteps x natoms x 3.
        Initialized as FileContents prior to file reading.
    """

    def __init__(self, path: Union[Path, str], natoms: int):

        super().__init__(path)
        self.natoms = natoms
        self.forces = FileContents

    def _read_file(self):

        forces = []

        with open(self.path, "r") as f:

            one_timestep_forces = []
            counter = 0

            for line in f:

                # note that atom index is 1-indexed
                # seems like the ordering of IQA_FORCES is not affected by OpenMP
                cartesian_forces = line.strip().split()[1:]
                cartesian_forces = list(map(float, cartesian_forces))
                one_timestep_forces.append(cartesian_forces)
                counter += 1

                if counter == self.natoms:
                    forces.append(one_timestep_forces)
                    one_timestep_forces = []
                    counter = 0

            # save as array of shape ntimesteps x natoms x 3
            self.forces = np.array(forces)
