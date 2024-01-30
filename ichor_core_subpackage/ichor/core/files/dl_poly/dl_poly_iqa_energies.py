from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.files.file import FileContents, ReadFile


class DlPolyIQAEnergies(ReadFile):
    """READS the IQA_ENERGIES file from FFLUX.

    :param path: Path to IQA_ENERGIES file

    :ivar natoms: Number of atoms in system
    :ivar energies: Array of shape ntimesteps x natoms for read energies
    """

    _filetype = ""

    def __init__(self, path: Union[Path, str]):

        super().__init__(path)
        self.energies = FileContents

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.stem == "IQA_ENERGIES"

    def _read_file(self):

        energies = []

        with open(self.path, "r") as f:

            lines = [i.strip().split() for i in f.readlines()]
            # lambda func that maps first argument as int and others as float
            map_func = lambda x: [int(x[0]), *map(float, x[1:])]
            # list of lists. Each inner list has index, energy
            lines = list(map(map_func, lines))

            max_atom_idx = max(i[0] for i in lines)
            self.natoms = max_atom_idx

            one_timestep_energies = []
            counter = 0
            for line in lines:
                # note that atom index is 1-indexed
                # also if using OpenMP, these are not going to be ordered correctly
                # so need to reorder them every timestep
                atom_index, iqa_energy = line
                one_timestep_energies.append((atom_index, iqa_energy))
                counter += 1

                # once all of one timestep is read, then sort and add
                if counter == self.natoms:
                    one_timestep_energies = sorted(
                        one_timestep_energies, key=lambda tup: tup[0]
                    )
                    energies.append([tu[1] for tu in one_timestep_energies])
                    one_timestep_energies = []
                    counter = 0

            # save as matrix of ntimesteps x natoms
            self.energies = np.array(energies)
