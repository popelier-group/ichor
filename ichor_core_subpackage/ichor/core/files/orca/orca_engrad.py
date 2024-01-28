from pathlib import Path
from typing import Union

import numpy as np
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.constants import type2nuclear_charge

# from enum import Enum
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasData

nuclear_charge2type = {int(v): k for k, v in type2nuclear_charge.items()}


class OrcaEngrad(ReadFile, HasAtoms, HasData):

    filetype = ".engrad"

    """
    Reads file containing the gradient calculated by ORCA.

    References:
        https://sites.google.com/site/orcainputlibrary/home
        https://www.cup.uni-muenchen.de/oc/zipse/teaching/computational-chemistry-2/topics/a-typical-orca-output-file/
        https://www.orcasoftware.de/tutorials_orca/first_steps/input_output.html
        https://www.afs.enea.it/software/orca/orca_manual_4_2_1.pdf (note this is for version 4, not 5)
        version 5 manual, needs login:
        available in https://orcaforum.kofo.mpg.de/app.php/dlext/?view=detail&df_id=186
        https://orcaforum.kofo.mpg.de/viewtopic.php?f=8&t=7470&p=32102&hilit=atomic+force#p32102
    """

    def __init__(self, path: Union[Path, str]):

        super(ReadFile, self).__init__(path)
        self.global_forces = FileContents
        self.total_energy = FileContents
        self.atoms = FileContents

    @property
    def raw_data(self) -> dict:
        return {"global_forces": self.global_forces, "total_energy": self.total_energy}

    @property
    def gradient(self) -> np.ndarray:

        return -self.global_forces

    def _read_file(self):

        atoms = Atoms()
        forces = {}

        with open(self.path, "r") as f:
            # assume the first lines start with !
            # the next lines are optional commands with %
            # and finally the inputs

            for line in f:

                if "Number of atoms" in line:

                    line = next(f)
                    line = next(f)
                    natoms = int(line.strip())

                elif "The current total energy" in line:

                    line = next(f)
                    line = next(f)
                    total_energy = float(line.strip())

                elif "The current gradient" in line:

                    line = next(f)

                    gradient_array = []

                    # every atom has x,y,z forces so multiply by 3
                    for _ in range(3 * natoms):
                        line = next(f).strip()
                        gradient_array.append(float(line))

                    gradient_array = np.array(gradient_array).reshape(-1, 3)

                elif "The atomic numbers and current coordinates" in line:

                    line = next(f)
                    line = next(f)

                    while line.strip():
                        line_split = line.split()
                        line_split[0] = nuclear_charge2type[int(line_split[0])]
                        atoms.append(Atom(*line_split))
                        try:
                            line = next(f)
                        except StopIteration:
                            break

            for atom_name, atom_gradient in zip(atoms.atom_names, gradient_array):
                # the force is -ve of gradient
                forces[atom_name] = -atom_gradient

            self.global_forces = forces
            self.atoms = atoms
            self.total_energy = total_energy
