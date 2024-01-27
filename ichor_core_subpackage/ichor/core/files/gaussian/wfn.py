from pathlib import Path
from typing import Dict, List, Union

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.float import from_scientific_double
from ichor.core.common.functools import classproperty
from ichor.core.common.itertools import chunker
from ichor.core.common.str import split_by
from ichor.core.common.units import AtomicDistance
from ichor.core.files.file import FileContents, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms, HasData


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


class WFN(HasAtoms, HasData, ReadFile, WriteFile):
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, but must also implement a write method because
    AIMAll needs to know the method used in the WFN calculation, otherwise
    AIMAll can give the wrong results.

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

    def __init__(
        self,
        path: Union[Path, str],
        method: str = None,
    ):
        super(ReadFile, self).__init__(path)

        self.method = method or FileContents

        self.atoms = FileContents
        self.title = FileContents
        self.program = FileContents
        self.n_orbitals = FileContents
        self.n_primitives = FileContents
        self.n_nuclei = FileContents
        self.centre_assignments = FileContents
        self.type_assignments = FileContents
        self.primitive_exponents = FileContents
        self.molecular_orbitals = FileContents
        self.total_energy = FileContents
        self.virial_ratio = FileContents

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of a WFN file"""
        return ".wfn"

    @classproperty
    def property_names(self) -> List[str]:
        return ["energy", "wfn"]

    @property
    def raw_data(self) -> Dict[str, float]:
        return {"energy": self.total_energy, "virial_ratio": self.virial_ratio}

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information.
        This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""
        atoms = Atoms()
        with open(self.path, "r") as f:
            title = next(f).strip()

            header = next(f).split()
            program = header[0]
            n_orbitals = int(header[1])
            n_primitives = int(header[4])
            n_nuclei = int(header[6])
            # method is not written by Gaussian in wfn file, we have to modify wfn file so that aimall knows
            # what method was used in Gaussian calculation
            method = header[-1] if header[-1] != "NUCLEI" else FileContents

            line = next(f)
            while not line.startswith(r"CENTRE ASSIGNMENTS"):
                record = split_by(
                    line, [4, 4, 16, 12, 12, 12, 10], return_remainder=True
                )
                atom_type = record[0]
                x = float(record[3])
                y = float(record[4])
                z = float(record[5])
                _ = float(record[-1])  # nuclear charge, not used
                atoms.add(
                    Atom(
                        atom_type,
                        x,
                        y,
                        z,
                        units=AtomicDistance.Bohr,
                    )
                )
                line = next(f)

            centre_assignments = []
            while not line.startswith(r"TYPE ASSIGNMENTS"):
                centre_assignments.extend(list(map(int, line.split()[2:])))
                line = next(f)

            type_assignments = []
            while not line.startswith(r"EXPONENTS"):
                type_assignments.extend(list(map(int, line.split()[2:])))
                line = next(f)

            primitive_exponents = []
            while not line.startswith(r"MO"):
                primitive_exponents.extend(
                    list(map(from_scientific_double, line.split()[1:]))
                )
                line = next(f)

            molecular_orbitals = []
            while not line.startswith(r"END DATA"):
                record = line.split()
                imo = int(record[1])
                eigen_value = float(record[3])
                occupation_number = float(record[7])
                energy = float(record[11])

                primitives = []
                line = next(f)
                while not (line.startswith(r"MO") or line.startswith(r"END DATA")):
                    primitives.extend(list(map(from_scientific_double, line.split())))
                    line = next(f)
                molecular_orbitals.append(
                    MolecularOrbital(
                        imo,
                        eigen_value,
                        occupation_number,
                        energy,
                        primitives,
                    )
                )

            record = next(f).split()
            total_energy = float(record[3])
            virial_ratio = float(record[6])

        self.title = self.title or title
        self.program = self.program or program
        self.n_orbitals = self.n_orbitals or n_orbitals
        self.n_primitives = self.n_primitives or n_primitives
        self.n_nuclei = self.n_nuclei or n_nuclei
        self.method = self.method or method

        self.atoms = self.atoms or atoms
        self.centre_assignments = self.centre_assignments or centre_assignments
        self.type_assignments = self.type_assignments or type_assignments
        self.primitive_exponents = self.primitive_exponents or primitive_exponents
        self.molecular_orbitals = self.molecular_orbitals or molecular_orbitals

        self.total_energy = self.total_energy or total_energy
        self.virial_ratio = self.virial_ratio or virial_ratio

    def _write_file(self, path: Path):
        """Write method needs to be implemented because the correct functional needs to be added to the .wfn file,
        so that AIMAll can then use it when it does calculations.
        Otherwise, the wrong results are obtained with AIMAll.
        """

        write_str = ""

        write_str += f"{self.title}\n"
        header_line = f"{self.program:16s} {self.n_orbitals:6d} MOL ORBITALS {self.n_primitives:6d} PRIMITIVES {self.n_nuclei:8d} NUCLEI"  # noqa E501
        # add method here, so that AIMAll works correctly
        # note that only selected functionals / methods work

        # do not modify header line with method if the method is HF
        if self.method.upper() != "HF":
            header_line += f"   {self.method}"

        write_str += f"{header_line}\n"
        for i, atom in enumerate(self.atoms):
            write_str += f"{atom.type:3s} {i+1:4d}    (CENTRE {i+1:2d}) {atom.x:12.8f}{atom.y:12.8f}{atom.z:12.8f}  CHARGE = {atom.nuclear_charge:3.1f}\n"  # noqa E501

        for centre_assignments in chunker(self.centre_assignments, 20):
            write_str += f"CENTRE ASSIGNMENTS  {''.join(map(lambda x: f'{x:3d}', centre_assignments))}\n"

        for type_assignments in chunker(self.type_assignments, 20):
            write_str += f"TYPE ASSIGNMENTS    {''.join(map(lambda x: f'{x:3d}', type_assignments))}\n"

        for exponents in chunker(self.primitive_exponents, 5):
            exponents = "".join(map(lambda x: f"{x:14.7E}", exponents)).replace(
                "E", "D"
            )
            write_str += f"EXPONENTS {exponents}\n"

        for molecular_orbital in self.molecular_orbitals:
            write_str += f"MO {molecular_orbital.index:4d}     MO {molecular_orbital.eigen_value:10.8f} OCC NO = {molecular_orbital.occupation_number:12.7f}  ORB. ENERGY ={molecular_orbital.energy:12.6f}\n"  # noqa E501
            for primitives in chunker(molecular_orbital.primitives, 5):
                primitives = "".join(map(lambda x: f"{x:16.8E}", primitives)).replace(
                    "E", "D"
                )
                write_str += f"{primitives}\n"

        write_str += "END DATA\n"
        write_str += f" TOTAL ENERGY ={self.total_energy:22.12f} THE VIRIAL(-V/T)= {self.virial_ratio:12.8f}"

        return write_str
