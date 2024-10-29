from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.types.multipole_moments import (
    MolecularDipole,
    MolecularQuadrupole,
)

from ichor.core.common.units import AtomicDistance
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasData


class OrcaOutput(HasAtoms, HasData, ReadFile):
    """Wraps around an .orcaoutput file that is the output of ORCA.
    Contains information such as coordinates (in Angstroms) and molecular
    dipoles and quadrupoles.
    
    :param path: Path object or string to the .orcaoutput file that are ORCA output files
    """

    _filetype = ".orcaoutput"

    def __init__(
        self,
        path: Union[Path, str],
    ):
        self.charge = FileContents
        self.multiplicity = FileContents
        self.atoms = FileContents
        self.center_of_mass = FileContents
        self.molecular_dipole = FileContents
        self.molecular_quadrupole = FileContents
        super(ReadFile, self).__init__(path)

    # TODO: implement
    @property
    def raw_data(self) -> dict:
        return {
            "center_of_mass": self.center_of_mass,
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "molecular_dipole": self.molecular_dipole,
            "molecular_quadrupole": self.molecular_quadrupole,
        }

    def _read_file(self):
        """Parse through a .orcaoutput file to look for the relevant information.
        This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""

        atoms = Atoms()

        # orca uses the center of mass for the multipole calculations
        # cclib seems to convert  this, so that the center of mass is 0 0 0

        # cclib does not parse quadrupole moment, so do not use it
        # also, orca doesn't seem to do higher multipole moments

        # TODO: finish implementation
        with open(self.path, "r") as f:

            for line in f:

                if "CARTESIAN COORDINATES (ANGSTROEM)" in line:

                    line = next(f)
                    line = next(f)

                    while line.strip():
                        l = line.split()
                        atom_type = l[0]
                        x = float(l[1])
                        y = float(l[2])
                        z = float(l[3])
                        atoms.add(
                            Atom(
                                atom_type,
                                x,
                                y,
                                z,
                                units=AtomicDistance.Angstroms,
                            )
                        )
                        line = next(f)

                elif "Total Charge" in line:
                    charge = int(line.strip().split()[-1])

                elif "Multiplicity" in line:
                    multiplicity = int(line.strip().split()[-1])

                elif "The origin for moment calculation is the CENTER OF MASS" in line:

                    ctr_of_mass_list = line.split()[-3:]
                    ctr_x = float(ctr_of_mass_list[0].replace("(", "").replace(",", ""))
                    ctr_y = float(ctr_of_mass_list[1])
                    ctr_z = float(ctr_of_mass_list[2].replace(")", ""))

                elif "Total Dipole Moment" in line:

                    tmp_dipole_moment = list(map(float, line.split()[-3:]))
                    dipole_moment = MolecularDipole(*tmp_dipole_moment)

                # note that this is optional
                # might not be in the output file
                elif "QUADRUPOLE MOMENT (A.U.)" in line:

                    line = next(f)  # ----
                    line = next(f)  # blank
                    line = next(f)  # XX YY ..
                    line = next(f)  # nuc
                    line = next(f)  # el
                    # quadrupole line in atomic units
                    line = next(f)
                    # quadrupole line in Buckingham, same as Debye Angstrom
                    line = next(f)
                    tmp_quadrupole_moment = list(map(float, line.split()[:6]))
                    self.molecular_quadrupole = MolecularQuadrupole(
                        *tmp_quadrupole_moment
                    )

        self.charge = charge
        self.multiplicity = multiplicity
        self.atoms = atoms
        self.center_of_mass = np.array([ctr_x, ctr_y, ctr_z])
        self.molecular_dipole = dipole_moment
