from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
from ichor.core.atoms import Atom, Atoms

# a bond is counted when two atoms are closer than this factor times the sum of their
# covalent radii. Same criterion (and factor) as
# ichor.core.calculators.connectivity.connectivity_calculator_distance, reimplemented here
# because that one is a Python double loop over every atom pair, which a condensed phase
# box of several thousand atoms makes far too slow.
BOND_RADIUS_FACTOR = 1.25

# how many atoms' worth of pairwise distances to work out at a time. The full N x N distance
# matrix of a large box does not need to be held in memory, only the (few) bonds found in
# it, so the pairs are worked through in row blocks of this many atoms.
DISTANCE_CHUNK_SIZE = 512


@dataclass
class MolecularSpecies:
    """One molecular type of a DL_POLY system: the template geometry of a single molecule
    of it, the FFLUX system name its models were trained under, and how many copies of it
    the simulation box holds.

    :param system_name: The name of the chemical system the molecule's models were trained
        under. This is what the CONFIG atom labels are prefixed with
        (``<system_name>_<atom>``) and what names the molecular type in the FIELD and
        MPOLES files.
    :param atoms: An ``Atoms`` instance holding *one* molecule of this species, whose atom
        indices run 1..natoms. Every copy of the species in the box is expected to list its
        atoms in the same order as this template.
    :param nummols: The number of copies of this species in the simulation box.
    """

    system_name: str
    atoms: Atoms
    nummols: int

    @property
    def natoms(self) -> int:
        """The number of atoms in one molecule of this species."""
        return len(self.atoms)

    @property
    def total_atoms(self) -> int:
        """The number of atoms all copies of this species contribute to the box."""
        return self.natoms * self.nummols

    @property
    def atom_names(self) -> List[str]:
        """The names (type + position, e.g. ``C1``, ``H2``) of the atoms of one molecule of
        this species. These are the names the species' model files are made for."""
        return [atom.name for atom in self.atoms]

    @property
    def formula(self) -> str:
        """The molecular formula of this species (e.g. ``NH3``), for naming it in messages
        while it does not yet have a system name of its own. The elements come in the order
        they first appear in the molecule, since that (rather than any convention) is the
        order the geometry lists them in."""
        types = [atom.type for atom in self.atoms]
        formula = ""
        for atom_type in dict.fromkeys(types):
            count = types.count(atom_type)
            formula += atom_type if count == 1 else f"{atom_type}{count}"
        return formula


@dataclass
class MolecularComposition:
    """The molecular make-up of a DL_POLY simulation box: which species it holds and which
    atoms of the box each individual molecule is made of.

    DL_POLY assigns the atoms of the CONFIG file to the molecules declared in the FIELD file
    strictly in order, so the molecules are kept in the order they are written out in and
    every atom of the box belongs to exactly one of them.

    :param species: The molecular types in the box, in the order they are declared in the
        FIELD file (which is the order their molecules appear in the CONFIG file).
    :param molecules: One entry per molecule in the box, in CONFIG order, holding the index
        of its species in ``species`` and the (0-based) indices of its atoms in the
        ``Atoms`` instance the composition was built from.
    """

    species: List[MolecularSpecies]
    molecules: List[Tuple[int, List[int]]]

    @property
    def total_atoms(self) -> int:
        """The total number of atoms in the box."""
        return sum(species.total_atoms for species in self.species)

    @property
    def nmolecules(self) -> int:
        """The total number of molecules in the box."""
        return len(self.molecules)

    def __str__(self):
        # a species which has not been named yet (see with_system_names) is named by its
        # formula instead, which is all that is known about it
        return ", ".join(
            f"{species.nummols} x {species.system_name or species.formula} "
            f"({species.natoms} atoms)"
            for species in self.species
        )

    def with_system_names(self, system_names: Sequence[str]) -> "MolecularComposition":
        """Returns the same composition with its species named, e.g. once the models the
        species are simulated with have been read.

        :param system_names: One name per species, in the order of ``species``.
        :raises ValueError: If as many names are not given as there are species.
        """
        if len(system_names) != len(self.species):
            raise ValueError(
                f"{len(system_names)} system name(s) were given "
                f"({', '.join(system_names)}) but the composition holds "
                f"{len(self.species)} molecular species: {self}"
            )
        return MolecularComposition(
            species=[
                MolecularSpecies(
                    system_name=system_name,
                    atoms=species.atoms,
                    nummols=species.nummols,
                )
                for species, system_name in zip(self.species, system_names)
            ],
            molecules=self.molecules,
        )


def bonded_neighbours(atoms: Atoms) -> List[np.ndarray]:
    """Returns, for every atom, the (0-based) indices of the atoms it is bonded to.

    Two atoms count as bonded when they are closer together than ``BOND_RADIUS_FACTOR``
    times the sum of their covalent radii, the same criterion
    :func:`ichor.core.calculators.connectivity.connectivity_calculator_distance` uses. Only
    the neighbours are kept (not the full connectivity matrix) and the distances are worked
    out in blocks of rows, so a box of several thousand atoms stays cheap in both time and
    memory.

    :param atoms: The ``Atoms`` instance to find the bonds of.
    :return: A list with one array of neighbour indices per atom.
    """

    atoms = atoms.to_angstroms()
    coordinates = np.array(atoms.coordinates, dtype=float)
    radii = np.array([atom.radius for atom in atoms], dtype=float)
    natoms = len(atoms)

    # squared distances via |a - b|^2 = |a|^2 + |b|^2 - 2 a.b, which needs only one
    # (chunk x natoms) array rather than the (chunk x natoms x 3) of differences
    square_norms = (coordinates**2).sum(axis=1)

    neighbours = []
    for start in range(0, natoms, DISTANCE_CHUNK_SIZE):
        end = min(start + DISTANCE_CHUNK_SIZE, natoms)
        square_distances = (
            square_norms[start:end, None]
            + square_norms[None, :]
            - 2.0 * (coordinates[start:end] @ coordinates.T)
        )
        maximum_distances = BOND_RADIUS_FACTOR * (
            radii[start:end, None] + radii[None, :]
        )
        bonded = square_distances < maximum_distances**2
        # an atom is not bonded to itself
        bonded[np.arange(end - start), np.arange(start, end)] = False
        for row in range(end - start):
            neighbours.append(np.flatnonzero(bonded[row]))

    return neighbours


def group_atoms_into_molecules(atoms: Atoms) -> List[List[int]]:
    """Groups the atoms of a geometry into molecules, i.e. into the connected components of
    its connectivity graph.

    :param atoms: The ``Atoms`` instance to split into molecules.
    :return: A list with one (sorted) list of 0-based atom indices per molecule. The
        molecules come in the order of their lowest-numbered atom, so a box written out
        molecule by molecule (as Packmol writes them) keeps the order it is stored in.
    """

    neighbours = bonded_neighbours(atoms)
    natoms = len(atoms)

    seen = [False] * natoms
    molecules = []
    for start in range(natoms):
        if seen[start]:
            continue
        # depth-first search over the bonds to collect one whole molecule
        stack = [start]
        molecule = []
        while stack:
            atom_index = stack.pop()
            if seen[atom_index]:
                continue
            seen[atom_index] = True
            molecule.append(atom_index)
            for other in neighbours[atom_index]:
                if not seen[other]:
                    stack.append(int(other))
        molecules.append(sorted(molecule))

    return molecules


def _molecule_signature(atoms: Atoms, atom_indices: Sequence[int]) -> Tuple[str, ...]:
    """Returns the signature two molecules have in common when they are copies of the same
    species: the sequence of their atom types. The order matters as well as the counts,
    because the atoms of a molecule are matched to its species' models by position.

    .. note::
        Two different species which happen to be made of the same atom types in the same
        order (i.e. isomers of one another) are indistinguishable by this signature and are
        collected into one species.
    """
    return tuple(atoms[atom_index].type for atom_index in atom_indices)


def _species_template(atoms: Atoms, atom_indices: Sequence[int]) -> Atoms:
    """Builds the one-molecule template of a species out of the atoms of one of its
    molecules, numbered 1..natoms so that its atom names (``C1``, ``H2``, ...) are the ones
    the species' model files were made for."""
    template = Atoms()
    for atom_index in atom_indices:
        atom = atoms[atom_index]
        template.add(Atom(atom.type, atom.x, atom.y, atom.z, units=atom.units))
    return template


def infer_molecular_composition(
    atoms: Atoms, system_names: Optional[Sequence[str]] = None
) -> MolecularComposition:
    """Works out the molecular composition of a simulation box from the geometry alone: the
    box is split into molecules along its bonds, molecules made of the same sequence of atom
    types are collected into a species, and the species are counted.

    This is what makes a Packmol box usable without being told what is in it - the number of
    species, how many atoms each of their molecules has, and how many copies of each the box
    holds all follow from the geometry.

    :param atoms: The ``Atoms`` instance holding the whole simulation box.
    :param system_names: The name to give each species, in the order the species first
        appear in the box. If ``None`` (default), the species are left unnamed, for the
        caller to fill in from the models it is going to use (see
        :meth:`MolecularComposition.with_system_names`).
    :raises ValueError: If as many names are not given as there are species in the box.
    :return: The composition of the box.
    """

    molecules = group_atoms_into_molecules(atoms)

    # collect the molecules into species, keeping the species in the order they first
    # appear in the box so that the CONFIG file can be written in the box's own order
    signatures: List[Tuple[str, ...]] = []
    species_templates: List[Atoms] = []
    species_counts: List[int] = []
    species_of_molecule: List[int] = []

    for atom_indices in molecules:
        signature = _molecule_signature(atoms, atom_indices)
        if signature in signatures:
            species_index = signatures.index(signature)
            species_counts[species_index] += 1
        else:
            species_index = len(signatures)
            signatures.append(signature)
            species_templates.append(_species_template(atoms, atom_indices))
            species_counts.append(1)
        species_of_molecule.append(species_index)

    species = [
        MolecularSpecies(system_name="", atoms=template, nummols=count)
        for template, count in zip(species_templates, species_counts)
    ]

    # DL_POLY reads the CONFIG atoms into the molecules declared in the FIELD file in order,
    # so all the molecules of a species have to be written out together, species by species,
    # in the order the FIELD file declares them
    ordered_molecules = [
        (species_index, molecules[molecule_index])
        for species_index in range(len(species))
        for molecule_index, molecule_species in enumerate(species_of_molecule)
        if molecule_species == species_index
    ]

    composition = MolecularComposition(species=species, molecules=ordered_molecules)

    if system_names is not None:
        composition = composition.with_system_names(system_names)

    return composition
