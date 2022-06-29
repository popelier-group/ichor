from pathlib import Path
from typing import Union, Optional, List, Dict
import numpy as np

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.common.str import split_by
from ichor.core.constants import AIMALL_FUNCTIONALS
from ichor.core.files.file import FileContents, ReadFile, WriteFile, File
from ichor.core.files.file_data import HasAtoms, HasProperties
from ichor.core.units import AtomicDistance
from ichor.core.common.itertools import chunker
from decimal import Decimal
from ichor.core.common.float import from_scientific_double


class MolecularOrbital:
    def __init__(
        self,
        index: int,
        eigen_value: float,
        occupation_number: float,
        energy: float,
        primitives: np.ndarray,
    ):
        self.index: int = index
        self.eigen_value: float = eigen_value
        self.occupation_number: float = occupation_number
        self.energy: float = energy
        self.primitives: np.ndarray = primitives


class WFN(HasAtoms, HasProperties, ReadFile, WriteFile, File):
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, so it does not have a write method.

    :param path: Path object or string to the .wfn file
    :param method: The method (eg. B3LYP) which was used in the Gaussian calculation
        that created the .wfn file. The method is not initially written to the .wfn
        file by Gaussian, but it is necessary to add it to the .wfn file because
        AIMAll does not automatically determine the method itself, so it can lead
        to wrong IQA/multipole moments results. To make sure AIMAll results are correct,
        the method is a required argument.
    :param mol_orbitals: The number of molecular orbitals to be read in from the .wfn file.
    :param primitives: The number of primitives to be read in from the .wfn file.
    :param nuclei: The number of nuclei in the system to be read in from the .wfn file.
    :param energy: The molecular energy read in from the bottom of the .wfn file
    :param virial: The virial read in from the bottom of the .wfn file
    :param atoms: an Atoms instance which is read in from the top of the .wfn file.
        Note that the units of the .wfn file are in Bohr.
    """

    def __init__(
        self,
        path: Union[Path, str],
        atoms: Optional[Atoms] = None,
    ):
        File.__init__(self, path)
        HasAtoms.__init__(self, atoms)

        self.title: str = FileContents
        self.program: str = FileContents

        self.n_orbitals: int = FileContents
        self.n_primitives: int = FileContents
        self.n_nuclei: int = FileContents
        self.method: str = FileContents

        self.centre_assignments: List[int] = FileContents
        self.type_assignments: List[int] = FileContents

        self.primitive_exponents: np.ndarray = FileContents
        self.molecular_orbitals: List[MolecularOrbital] = FileContents

        self.total_energy: float = FileContents
        self.virial_ratio: float = FileContents

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""
        atoms = Atoms()
        with open(self.path, "r") as f:
            title = next(f).strip()

            header = next(f).split()
            program = header[0]
            n_orbitals = int(header[1])
            n_primitives = int(header[4])
            n_nuclei = int(header[6])
            method = header[7] if len(header) >= 8 else "HF"

            line = next(f)
            while not line.startswith(r"CENTRE ASSIGNMENTS"):
                record = split_by(
                    line, [4, 4, 16, 12, 12, 12, 10], return_remainder=True
                )
                atom_type = record[0]
                x = float(record[3])
                y = float(record[4])
                z = float(record[5])
                charge = float(record[-1])
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
            centre_assignments = np.array(centre_assignments)

            type_assignments = []
            while not line.startswith(r"EXPONENTS"):
                type_assignments.extend(list(map(int, line.split()[2:])))
                line = next(f)
            type_assignments = np.array(type_assignments)

            exponents = []
            while not line.startswith(r"MO"):
                exponents.extend(
                    list(map(from_scientific_double, line.split()[1:]))
                )
                line = next(f)
            primitive_exponents = np.array(exponents)

            molecular_orbitals = []
            while not line.startswith(r"END DATA"):
                record = line.split()
                imo = int(record[1])
                eigen_value = float(record[3])
                occupation_number = float(record[7])
                energy = float(record[11])

                primitives = []
                line = next(f)
                while not (
                    line.startswith(r"MO") or line.startswith(r"END DATA")
                ):
                    primitives.extend(
                        list(map(from_scientific_double, line.split()))
                    )
                    line = next(f)
                molecular_orbitals.append(
                    MolecularOrbital(
                        imo,
                        eigen_value,
                        occupation_number,
                        energy,
                        np.array(primitives),
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
        self.primitive_exponents = self.primitive_exponents or exponents
        self.molecular_orbitals = self.molecular_orbitals or molecular_orbitals

        self.total_energy = self.total_energy or total_energy
        self.virial_ratio = self.virial_ratio or virial_ratio

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of a WFN file"""
        return ".wfn"

    @property
    def properties(self) -> Dict[str, float]:
        return {"energy": self.total_energy, "virial_ratio": self.virial_ratio}

    def _write_file(self, path: Path):
        with open(path, "w") as f:
            f.write(f"{self.title}\n")
            header_line = f"{self.program:16s} {self.n_orbitals:6d} MOL ORBITALS {self.n_primitives:6d} PRIMITIVES {self.n_nuclei:8d} NUCLEI"
            if self.method in AIMALL_FUNCTIONALS:
                header_line += f"   {self.method}"
            f.write(f"{header_line}\n")
            for i, atom in enumerate(self.atoms):
                f.write(
                    f"{atom.type:3s} {i+1:4d}    (CENTRE {i+1:2d}) {atom.x:12.8f}{atom.y:12.8f}{atom.z:12.8f}  CHARGE = {atom.nuclear_charge:3.1f}\n"
                )

            for centre_assignments in chunker(self.centre_assignments, 20):
                f.write(
                    f"CENTRE ASSIGNMENTS  {''.join(map(lambda x: f'{x:3d}', centre_assignments))}\n"
                )

            for type_assignments in chunker(self.type_assignments, 20):
                f.write(
                    f"TYPE ASSIGNMENTS    {''.join(map(lambda x: f'{x:3d}', type_assignments))}\n"
                )

            for exponents in chunker(self.primitive_exponents, 5):
                exponents = "".join(
                    map(lambda x: f"{x:14.7E}", exponents)
                ).replace("E", "D")
                f.write(f"EXPONENTS {exponents}\n")

            for molecular_orbital in self.molecular_orbitals:
                f.write(
                    f"MO {molecular_orbital.index:4d}     MO {molecular_orbital.eigen_value:10.8f} OCC NO = {molecular_orbital.occupation_number:12.7f}  ORB. ENERGY ={molecular_orbital.energy:12.6f}\n"
                )
                for primitives in chunker(molecular_orbital.primitives, 5):
                    primitives = "".join(
                        map(lambda x: f"{x:16.8E}", primitives)
                    ).replace("E", "D")
                    f.write(f"{primitives}\n")

            f.write("END DATA\n")
            f.write(
                f" TOTAL ENERGY ={self.total_energy:22.12f} THE VIRIAL(-V/T)= {self.virial_ratio:12.8f}"
            )
