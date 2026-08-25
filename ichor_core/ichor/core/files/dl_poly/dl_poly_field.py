from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from ichor.core.atoms import Atom, Atoms
from ichor.core.calculators import default_connectivity_calculator
from ichor.core.calculators.geometry_calculator import get_internal_feature_indices
from ichor.core.common.constants import dlpoly_weights
from ichor.core.files.dl_poly.dl_poly_composition import (
    MolecularComposition,
    MolecularSpecies,
)
from ichor.core.files.file import WriteFile


class ConnectedAtom(Atom):
    def __init__(self, atom: Atom, parent: "ConnectedAtoms"):
        super().__init__(
            atom.type,
            atom.x,
            atom.y,
            atom.z,
            index=atom.index,
            parent=parent,
            units=atom.units,
        )
        self.bond_list = []
        self.angle_list = []
        self.dihedral_list = []

    def set_bond(self, other: Atom):
        self.bond_list += [other]

    def set_angle(self, other: Atom):
        self.angle_list += [other]

    def set_dihedral(self, other: Atom):
        self.dihedral_list += [other]


class ConnectedAtoms(Atoms):
    def __init__(self, atoms):
        super().__init__()
        for atom in atoms:
            self.add(ConnectedAtom(atom, self))

        self._bonds = []
        self._angles = []
        self._dihedrals = []

        bonds = np.array(self.connectivity(default_connectivity_calculator))
        angles = np.matmul(bonds, bonds)
        dihedrals = np.matmul(angles, bonds)

        bond_list = []
        angle_list = []
        dihedral_list = []

        # iterate over upper triangular matrix to avoid double counting
        for i in range(bonds.shape[0]):
            for j in range(i + 1, bonds.shape[1]):
                if bonds[i, j] == 1:
                    bond_list += [(i, j)]
                elif angles[i, j] == 1:
                    angle_list += [(i, j)]
                elif dihedrals[i, j] == 1:
                    dihedral_list += [(i, j)]

        for i, j in bond_list:
            self[i].set_bond(self[j])
            self[j].set_bond(self[i])
            self._bonds.append((i, j))

        for i, j in angle_list:
            for k in list(set(self[i].bond_list) & set(self[j].bond_list)):
                self[i].set_angle(self[j])
                self[j].set_angle(self[i])
                self._angles.append((i, k.i, j))

        for i, j in dihedral_list:
            iatoms = list(set(self[i].bond_list) & set(self[j].angle_list))
            jatoms = list(set(self[j].bond_list) & set(self[i].angle_list))
            for k in iatoms:
                for l in jatoms:
                    if k in self[l.i].bond_list:
                        self[i].set_dihedral(self[j])
                        self[j].set_dihedral(self[i])
                        self._dihedrals.append((i, k.i, l.i, j))
                        break

    @property
    def bonds(self):
        return [(i + 1, j + 1) for i, j in self._bonds]

    @property
    def angles(self):
        return [(i + 1, j + 1, k + 1) for i, j, k in self._angles]

    @property
    def dihedrals(self):
        return [(i + 1, j + 1, k + 1, l + 1) for i, j, k, l in self._dihedrals]

    def bond_names(self) -> List[str]:
        return [f"{self[i].name}-{self[j].name}" for i, j in self._bonds]

    def angle_names(self) -> List[str]:
        return [
            f"{self[i].name}-{self[j].name}-{self[k].name}" for i, j, k in self._angles
        ]

    def dihedral_names(self) -> List[str]:
        return [
            f"{self[i].name}-{self[j].name}-{self[k].name}-{self[l].name}"
            for i, j, k, l in self._dihedrals
        ]

    def names(self):
        return (
            self.bond_names(),
            self.angle_names(),
            self.dihedral_names(),
        )


class DlPolyField(WriteFile):
    """Write out a DL_POLY FIELD file, which declares the molecular types of the system.

    :param system_name: The name of the chemical system, which names the (single) molecular
        type. Ignored (in favour of the name of each species) when a ``composition`` is given.
    :param atoms: The atoms of one molecule of the system. Ignored (in favour of each
        species' own template) when a ``composition`` is given.
    :param path: The path to the FIELD file, defaults to ``Path("FIELD")``.
    :param nummols: The number of molecules of the (single) molecular type, defaults to 1.
        Ignored (in favour of each species' own count) when a ``composition`` is given.
    :param multipolar: The highest multipole interaction order (L') for FFLUX
        electrostatics, written as a ``Multipolar <L'>`` line. ``None`` (default) omits the
        line, i.e. a pure-IQA run.
    :param all_pairs_bonds: Whether to list every intramolecular atom pair as a
        (zero-constant) bond rather than just the chemically bonded pairs plus angles and
        dihedrals, see below.
    :param composition: The molecular composition of the system (see
        :class:`ichor.core.files.dl_poly.MolecularComposition`), used when it holds more than
        one kind of molecule and/or many copies of them - as a condensed phase box out of
        Packmol does. One molecular type is then declared per species, each with its own
        name, its own ``nummols`` count and the bonded terms of a *single* molecule of it
        (which is what DL_POLY expects: the terms are declared once and applied to every copy
        of the molecule). If ``None`` (default), a single molecular type is declared from
        ``system_name``, ``atoms`` and ``nummols``.
    """

    _filetype = ""

    def __init__(
        self,
        system_name: str,
        atoms: Atoms,
        path: Union[Path, str] = Path("FIELD"),
        nummols=1,
        multipolar: Optional[int] = None,
        all_pairs_bonds: bool = False,
        composition: Optional[MolecularComposition] = None,
    ):

        super().__init__(path)

        self.system_name = system_name
        self.atoms = atoms
        self.nummols = nummols
        self.composition = composition
        # highest multipole interaction order (L') for FFLUX electrostatics, written as a
        # "Multipolar <L'>" line. None (default) omits the line, i.e. a pure-IQA run.
        self.multipolar = multipolar
        # when True, list every INTRA-molecular atom pair as a (zero-constant) bond instead
        # of just the chemically bonded pairs + angles + dihedrals. "Intra-molecular" means
        # within each molecule (connected component of the connectivity graph): all pairs
        # inside a molecule are bonded/excluded, but pairs BETWEEN molecules are left active.
        # This puts every intramolecular pair on DL_POLY's exclusion list, which is required
        # for FFLUX multipole runs so the explicit multipole electrostatics act only BETWEEN
        # molecules (the intramolecular energy is already in the IQA models). Otherwise
        # distant intramolecular pairs get spurious multipole interactions that diverge as
        # atoms approach. For a single molecule this is simply every pair; for a cluster
        # (e.g. a water n-mer) it is every pair within each molecule, keeping the crucial
        # inter-molecular electrostatics (e.g. hydrogen bonds) intact.
        self.all_pairs_bonds = all_pairs_bonds

    def _molecule_atom_indices(self) -> List[List[int]]:
        """Group the (0-based) atom indices into molecules, i.e. connected components of the
        connectivity graph. Used to build the per-molecule intramolecular exclusion bonds."""
        connectivity = np.array(
            self.atoms.connectivity(default_connectivity_calculator)
        )
        natoms = len(self.atoms)
        seen = [False] * natoms
        components = []
        for start in range(natoms):
            if seen[start]:
                continue
            # depth-first search over the connectivity matrix to collect one molecule
            stack = [start]
            component = []
            while stack:
                atom_index = stack.pop()
                if seen[atom_index]:
                    continue
                seen[atom_index] = True
                component.append(atom_index)
                for other in range(natoms):
                    if connectivity[atom_index, other] and not seen[other]:
                        stack.append(other)
            components.append(sorted(component))
        return components

    # TODO: implement reading for dlpoly field file
    # def _read_file(self):
    #     ...

    @property
    def molecular_types(self) -> List[MolecularSpecies]:
        """The molecular types declared in the FIELD file: the species of the composition
        when there is one, otherwise the single type built from ``system_name``, ``atoms``
        and ``nummols``."""
        if self.composition is not None:
            return self.composition.species
        return [
            MolecularSpecies(
                system_name=self.system_name,
                atoms=self.atoms,
                nummols=self.nummols,
            )
        ]

    def _all_pairs_bonds(self, species: MolecularSpecies) -> List[tuple]:
        """Every pair of atoms of one molecular type as a zero-constant "bond", so that
        DL_POLY excludes all intra-molecular pairs from the nonbonded (multipole)
        electrostatics while inter-molecular pairs stay active. No angle or dihedral terms
        are needed since every intramolecular pair is already covered by a bond.

        With a composition each molecular type is a single molecule, so this is simply every
        pair of it. Without one, ``atoms`` may hold several molecules (e.g. a water n-mer
        making up one molecular type), so the pairs are taken within each molecule
        (connected component) only, keeping the inter-molecular electrostatics intact.
        """
        if self.composition is not None:
            components = [list(range(species.natoms))]
        else:
            components = self._molecule_atom_indices()

        bonds = []
        for component in components:
            for a in range(len(component)):
                for b in range(a + 1, len(component)):
                    # DL_POLY atom indices are 1-based
                    bonds.append((component[a] + 1, component[b] + 1))
        bonds.sort()
        return bonds

    def _molecular_type_block(self, species: MolecularSpecies) -> str:
        """The FIELD block declaring one molecular type: its name, how many copies of it the
        system holds, its atoms and its (zero-constant) bonded terms. The terms are declared
        for a single molecule of the type; DL_POLY applies them to every copy."""

        if self.all_pairs_bonds:
            bonds = self._all_pairs_bonds(species)
            angles = []
            dihedrals = []
        else:
            bonds, angles, dihedrals = get_internal_feature_indices(species.atoms)

        str_to_write = ""

        str_to_write += f"{species.system_name}\n"
        str_to_write += f"nummols {species.nummols}\n"
        str_to_write += f"atoms {species.natoms}\n"
        for atom in species.atoms:
            #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
            str_to_write += (
                f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
            )
        str_to_write += f"BONDS {len(bonds)}\n"
        for i, j in bonds:
            str_to_write += f"harm {i} {j} 0.0 0.0\n"
        if len(angles) > 0:
            str_to_write += f"ANGLES {len(angles)}\n"
            for i, j, k in angles:
                str_to_write += f"harm {i} {j} {k} 0.0 0.0\n"
        if len(dihedrals) > 0:
            str_to_write += f"DIHEDRALS {len(dihedrals)}\n"
            for i, j, k, l in dihedrals:
                str_to_write += f"harm {i} {j} {k} {l} 0.0 0.0\n"
        str_to_write += "finish\n"

        return str_to_write

    def _write_file(self, path: Path):

        molecular_types = self.molecular_types

        str_to_write = ""

        str_to_write += "DL_FIELD v3.00\n"
        str_to_write += "Units kJ/mol\n"
        # multipole electrostatics interaction order (omitted for a pure-IQA run)
        if self.multipolar is not None:
            str_to_write += f"Multipolar {self.multipolar}\n"
        str_to_write += f"Molecular types {len(molecular_types)}\n"
        # one block per molecular type, in the order DL_POLY reads the CONFIG atoms into
        for species in molecular_types:
            str_to_write += self._molecular_type_block(species)
        str_to_write += "close\n"

        return str_to_write
