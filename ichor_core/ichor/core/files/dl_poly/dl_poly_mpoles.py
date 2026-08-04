from pathlib import Path
from typing import Union

from ichor.core.atoms import Atoms
from ichor.core.files.file import WriteFile


class DlPolyMpoles(WriteFile):
    """Write out a DL_POLY ``MPOLES`` file, which is required for FFLUX multipole
    electrostatics runs (i.e. whenever a ``Multipolar`` line is present in the FIELD file).

    DL_POLY needs this file so that it can allocate the multipole moment arrays. The moment
    values written here are dummy placeholders (a charge and a dipole per atom) because
    FFLUX overwrites them with the values predicted by the kriging models at every timestep
    - only the presence and structure of the file matter, not the values.

    :param system_name: The name of the chemical system (used for the title and molecule name).
    :param atoms: An ``Atoms`` instance for one molecule; one moment block is written per atom.
    :param path: The path to the MPOLES file, defaults to ``Path("MPOLES")``.
    :param nummols: The number of molecules of this type, defaults to 1.
    """

    _filetype = ""

    def __init__(
        self,
        system_name: str,
        atoms: Atoms,
        path: Union[Path, str] = Path("MPOLES"),
        nummols: int = 1,
    ):

        super().__init__(path)

        self.system_name = system_name
        self.atoms = atoms
        self.nummols = nummols

    def _write_file(self, path: Path):

        str_to_write = ""

        # header - mirrors the top of the FIELD file (uppercase keywords)
        str_to_write += f"{self.system_name}\n"
        str_to_write += "MOLECULES 1\n"
        str_to_write += f"{self.system_name}\n"
        str_to_write += f"NUMMOLS {self.nummols}\n"
        str_to_write += f"ATOMS {len(self.atoms)}\n"
        str_to_write += "\n"

        # one block per atom: "<type> <order>" then a charge line and a dipole line. Order 1
        # (charge + dipole) is enough for DL_POLY to allocate the arrays; the values are
        # dummy placeholders overwritten by the FFLUX model predictions.
        for atom in self.atoms:
            str_to_write += f"{atom.type} 1\n"
            str_to_write += "  0.0\n"  # charge (monopole)
            str_to_write += "  0.0  0.0  0.0\n"  # dipole (x, y, z)
            str_to_write += "\n"

        str_to_write += "FINISH\n"
        str_to_write += "CLOSE\n"

        return str_to_write
