from pathlib import Path
from typing import List, Optional, Union

from ichor.core.atoms import Atoms
from ichor.core.files.dl_poly.dl_poly_composition import (
    MolecularComposition,
    MolecularSpecies,
)
from ichor.core.files.file import WriteFile


class DlPolyMpoles(WriteFile):
    """Write out a DL_POLY ``MPOLES`` file, which is required for FFLUX multipole
    electrostatics runs (i.e. whenever a ``Multipolar`` line is present in the FIELD file).

    DL_POLY needs this file so that it can allocate the multipole moment arrays. The moment
    values written here are dummy placeholders (a charge and a dipole per atom) because
    FFLUX overwrites them with the values predicted by the kriging models at every timestep
    - only the presence and structure of the file matter, not the values.

    :param system_name: The name of the chemical system (used for the title and molecule
        name). Ignored (in favour of the name of each species) when a ``composition`` is given.
    :param atoms: An ``Atoms`` instance for one molecule; one moment block is written per
        atom. Ignored (in favour of each species' own template) when a ``composition`` is given.
    :param path: The path to the MPOLES file, defaults to ``Path("MPOLES")``.
    :param nummols: The number of molecules of this type, defaults to 1. Ignored (in favour
        of each species' own count) when a ``composition`` is given.
    :param composition: The molecular composition of the system (see
        :class:`ichor.core.files.dl_poly.MolecularComposition`), used when it holds more than
        one kind of molecule and/or many copies of them. One molecule block is then written
        per species, mirroring the molecular types of the FIELD file (which is what DL_POLY
        matches this file up against). If ``None`` (default), a single molecule block is
        written from ``system_name``, ``atoms`` and ``nummols``.
    """

    _filetype = ""

    def __init__(
        self,
        system_name: str,
        atoms: Atoms,
        path: Union[Path, str] = Path("MPOLES"),
        nummols: int = 1,
        composition: Optional[MolecularComposition] = None,
    ):

        super().__init__(path)

        self.system_name = system_name
        self.atoms = atoms
        self.nummols = nummols
        self.composition = composition

    @property
    def molecular_types(self) -> List[MolecularSpecies]:
        """The molecules declared in the MPOLES file. These mirror the molecular types of
        the FIELD file, so they come from the composition when there is one."""
        if self.composition is not None:
            return self.composition.species
        return [
            MolecularSpecies(
                system_name=self.system_name,
                atoms=self.atoms,
                nummols=self.nummols,
            )
        ]

    def _write_file(self, path: Path):

        molecular_types = self.molecular_types

        str_to_write = ""

        # header - mirrors the top of the FIELD file (uppercase keywords). The title is the
        # name of the first molecule, which for a single-species system is the system itself.
        str_to_write += f"{molecular_types[0].system_name}\n"
        str_to_write += f"MOLECULES {len(molecular_types)}\n"

        for species in molecular_types:
            str_to_write += f"{species.system_name}\n"
            str_to_write += f"NUMMOLS {species.nummols}\n"
            str_to_write += f"ATOMS {species.natoms}\n"
            str_to_write += "\n"

            # one block per atom: "<type> <order>" then a charge line and a dipole line.
            # Order 1 (charge + dipole) is enough for DL_POLY to allocate the arrays; the
            # values are dummy placeholders overwritten by the FFLUX model predictions.
            for atom in species.atoms:
                str_to_write += f"{atom.type} 1\n"
                str_to_write += "  0.0\n"  # charge (monopole)
                str_to_write += "  0.0  0.0  0.0\n"  # dipole (x, y, z)
                str_to_write += "\n"

            str_to_write += "FINISH\n"

        str_to_write += "CLOSE\n"

        return str_to_write
