from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.files.file import FileContents, ReadFile


class DlPolyIQAEnergies(ReadFile):
    """READS the IQA_ENERGIES file from FFLUX.

    :param path: Path to IQA_ENERGIES file
    :param natoms: Number of atoms in the system.
    """

    def __init__(self, path: Union[Path, str], natoms: int):

        super().__init__(path)
        self.natoms = natoms
        self.energies = FileContents

    def _read_file(self):

        energies = []

        with open(self.path, "r") as f:

            one_timestep_energies = []
            counter = 0
            for line in f:
                # note that atom index is 1-indexed
                # also if using OpenMP, these are not going to be ordered correctly
                # so need to reorder them every timestep
                atom_index, iqa_energy = line.strip().split()
                atom_index, iqa_energy = int(atom_index), float(iqa_energy)
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

            # save as matrix of natoms x ntimesteps
            self.energies = np.array(energies)
