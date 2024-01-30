from pathlib import Path
from typing import Dict, Union

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.constants import type2nuclear_charge
from ichor.core.files.file import FileContents, FileState, ReadFile
from ichor.core.files.file_data import HasAtoms, HasData

nuclear_charge_to_type = {v: k for k, v in type2nuclear_charge.items()}


class MolecularOrbital:
    def __init__(
        self,
        index: int,
        eigen_value: float,
        occupation_number: float,
        energy: float,
        primitives: list,
    ):
        self.index = index
        self.eigen_value = eigen_value
        self.occupation_number = occupation_number
        self.energy = energy
        self.primitives = primitives


class WFX(HasAtoms, HasData, ReadFile):
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, so it does not have a write method.

    :param path: Path object or string to the .wfn file
    :param atoms: an Atoms instance which is read in from the top of the .wfn file.
        Note that the units of the .wfn file are in Bohr.
    :param method: The method (eg. B3LYP) which was used in the Gaussian calculation
        that created the .wfn file. The method is not initially written to the .wfn
        file by Gaussian, but it is necessary to add it to the .wfn file because
        AIMAll does not automatically determine the method itself, so it can lead
        to wrong IQA/multipole moments results. To make sure AIMAll results are correct,
        the method is a required argument.

    :ivar mol_orbitals: The number of molecular orbitals to be read in from the .wfn file.
    :ivar primitives: The number of primitives to be read in from the .wfn file.
    :ivar nuclei: The number of nuclei in the system to be read in from the .wfn file.
    :ivar energy: The molecular energy read in from the bottom of the .wfn file
    :ivar virial: The virial read in from the bottom of the .wfn file

    .. note::
        Since the wfn file is written out by Gaussian, we do not really
        have to modify it when writing out except we need to add the method used,
        so that AIMALL can use the correct method. Otherwise AIMAll assumes Hartree-Fock
        was used, which might be wrong.

    """

    filetype = ".wfx"

    def __init__(
        self,
        path: Union[Path, str],
        method: str = None,
    ):
        super(ReadFile, self).__init__(path)

        self.method = method or FileContents

        self.atoms = FileContents
        self.title = FileContents
        self.n_orbitals = FileContents
        self.n_primitives = FileContents
        self.n_nuclei = FileContents
        self.centre_assignments = FileContents
        self.type_assignments = FileContents
        self.primitive_exponents = FileContents
        self.molecular_orbitals = FileContents
        self.total_energy = FileContents
        self.virial_ratio = FileContents

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information.
        This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""

        atoms = Atoms()

        atom_names = []
        atom_coordinates = []

        with open(self.path, "r") as f:

            for line in f:

                if "<Title>" in line:
                    title = next(f).strip()

                elif "<Model>" in line:
                    method = next(f).strip()

                elif "<Number of Nuclei>" in line:
                    n_nuclei = int(next(f).strip())

                elif "<Number of Occupied Molecular Orbitals>" in line:
                    n_orbitals = int(next(f).strip())

                # elif "<Number of Perturbations>" in line:
                #     n_perturbations = int(next(f).strip())

                # elif "<Net Charge>" in line:
                #     net_charge = int(next(f).strip())

                # elif "<Number of Electrons>" in line:
                #     n_electrons = int(next(f).strip())

                # elif "<Electronic Spin Multiplicity>" in line:
                #     spin_multiplicity = int(next(f).strip())

                elif "<Atomic Numbers>" in line:
                    for _ in range(n_nuclei):
                        atom_names.append(nuclear_charge_to_type[int(next(f).strip())])

                elif "<Nuclear Cartesian Coordinates>" in line:
                    for _ in range(n_nuclei):
                        atom_coordinates.append(
                            list(map(float, next(f).strip().split()))
                        )

                elif "<Number of Primitives>" in line:
                    n_primitives = int(next(f).strip())

                elif "<Energy = T + Vne + Vee + Vnn>" in line:
                    total_energy = float(next(f).strip())

                elif "<Virial Ratio (-V/T)>" in line:
                    virial_ratio = float(next(f).strip())

        # make atoms instance
        for atom_type, atom_coord in zip(atom_names, atom_coordinates):
            atoms.append(Atom(atom_type, *atom_coord))

        self.title = self.title or title
        self.n_orbitals = self.n_orbitals or n_orbitals
        self.n_primitives = self.n_primitives or n_primitives
        self.n_nuclei = self.n_nuclei or n_nuclei
        self.method = self.method or method

        self.atoms = self.atoms or atoms
        # TODO: implement reading of these
        # self.centre_assignments = self.centre_assignments or centre_assignments
        # self.type_assignments = self.type_assignments or type_assignments
        # self.primitive_exponents = self.primitive_exponents or primitive_exponents
        # self.molecular_orbitals = self.molecular_orbitals or molecular_orbitals

        self.total_energy = self.total_energy or total_energy
        self.virial_ratio = self.virial_ratio or virial_ratio

    @property
    def properties(self) -> Dict[str, float]:
        return {"energy": self.total_energy, "virial_ratio": self.virial_ratio}

    def _check_values_before_writing(self):
        """This check is just here so that the file is read before attempting to write the file.
        This is to prevent a situation where the original file has not been read yet,
        but a new file with the same path is being written
        (so therefore the new file is empty and all the data has been
        lost and has not been read in into an instance yet).

        ..note::
            Even though the file could already be read in and some attributes might be modified by the user,
            reading the file a second time prior to writing will not change any user attributes because of the
            way the read file is written (i.e. any user-set attributes are kept even after the file is read again).
        """
        # TODO: potentially make this the default for WriteFile._check_values_before_writing
        if self.state == FileState.Unread:
            self.read()

    def _write_file(self, path: Path):
        """Write method needs to be implemented because the correct functional needs to be added to the .wfn file,
        so that AIMAll can then use it when it does calculations.
        Otherwise, the wrong results are obtained with AIMAll.
        """
        # TODO: implement
        pass
