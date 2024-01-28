import numpy as np
from ichor.core.atoms import Atoms
from ichor.core.common.constants import coulombbhrsquared_to_debye, coulombbohr_to_debye
from ichor.core.files import IntDirectory
from ichor.core.multipoles import (
    atomic_contribution_to_molecular_dipole,
    atomic_contribution_to_molecular_quadrupole,
    dipole_spherical_to_cartesian,
    quadrupole_spherical_to_cartesian,
)


def recover_molecular_dipole(
    atoms: Atoms,
    ints_dir: IntDirectory,
    atoms_in_angstroms=True,
    convert_to_debye=True,
    convert_to_cartesian=True,
):
    """
    Reads in a geometry (atoms) and _atomicfiles directory containing AIMAll output files
    and calculates the molecular dipole moment of the system (in spherical coordinates)
    from the AIMAll atomic multipole moments.

    .. note::
        Assumes atomic multipole moment units are atomic units (Coulomb Bohr) because this is what AIMAll gives.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an IntDirectory file instance, which wraps around an AIMAll output directory
    :param atoms_in_angstroms: Whether the Atom instance coordinates are in Bohr or Angstroms
        , defaults to True (meaning coordinates are in Angstroms)
    :param convert_to_debye: Whether or not to convert the final result to Debye, default to True.
        This converts from atomic units to Debye.
    :param convert_to_cartesian: Whether or not to convert the recovered molecular dipole from spherical
        to Cartesian, defaults to True. Note that Gaussian calculates molecular multipole moments
        in Cartesian coordinates, so set to True in case you are comparing against Gaussian.
    :returns: A numpy array containing the molecular dipole moment.
    """

    # make sure we are in Bohr
    if atoms_in_angstroms:
        atoms = atoms.to_bohr()

    molecular_dipole = np.zeros(3)

    for atom in atoms:

        # get necessary data for calculations
        atom_coords = atom.coordinates
        global_multipoles = ints_dir[atom.name].global_multipole_moments

        # get the values for a particular atom
        q00 = global_multipoles["q00"]
        q10 = global_multipoles["q10"]
        q11c = global_multipoles["q11c"]
        q11s = global_multipoles["q11s"]

        atomic_contibution = atomic_contribution_to_molecular_dipole(
            q00, q10, q11c, q11s, atom_coords
        )
        molecular_dipole += atomic_contibution

    if convert_to_debye:
        molecular_dipole *= coulombbohr_to_debye

    if convert_to_cartesian:
        molecular_dipole = dipole_spherical_to_cartesian(*molecular_dipole)

    return molecular_dipole


def recover_molecular_quadrupole(
    atoms: Atoms,
    ints_dir: IntDirectory,
    atoms_in_angstroms=True,
    convert_to_debye=True,
    convert_to_cartesian=True,
):
    """
    Reads in a geometry (atoms) and _atomicfiles directory containing AIMAll output files
    and calculates the molecular quadrupole moment of the system (in spherical coordinates)
    from the AIMAll atomic multipole moments.

    .. note::
        Assumes atomic multipole moment units are atomic units (Coulomb Bohr**2) because this is what AIMAll gives.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an IntDirectory file instance, which wraps around an AIMAll output directory
    :param atoms_in_angstroms: Whether the Atom instance coordinates are in Bohr or Angstroms
        , defaults to True (meaning coordinates are in Angstroms)
    :param convert_to_debye: Whether or not to convert the final result to Debye, default to True.
        This converts from atomic units to Debye.
    :param convert_to_cartesian: Whether or not to convert the recovered molecular quadrupole from spherical
        to Cartesian, defaults to True. Note that Gaussian calculates molecular multipole moments
        in Cartesian coordinates, so set to True in case you are comparing against Gaussian.
    :returns: A numpy array containing the molecular quadrupole moment.
    """

    # make sure we are in Bohr
    if atoms_in_angstroms:
        atoms = atoms.to_bohr()

    # spherical representation
    molecular_quadrupole = np.zeros(5)

    for atom in atoms:

        # get necessary data for calculations
        atom_coords = atom.coordinates
        global_multipoles = ints_dir[atom.name].global_multipole_moments

        # get the values for a particular atom
        q00 = global_multipoles["q00"]
        q10 = global_multipoles["q10"]
        q11c = global_multipoles["q11c"]
        q11s = global_multipoles["q11s"]
        q20 = global_multipoles["q20"]
        q21c = global_multipoles["q21c"]
        q21s = global_multipoles["q21s"]
        q22c = global_multipoles["q22c"]
        q22s = global_multipoles["q22s"]

        atomic_contibution = atomic_contribution_to_molecular_quadrupole(
            q00, q10, q11c, q11s, q20, q21c, q21s, q22c, q22s, atom_coords
        )
        molecular_quadrupole += atomic_contibution

    if convert_to_debye:
        molecular_quadrupole *= coulombbhrsquared_to_debye

    if convert_to_cartesian:
        molecular_quadrupole = quadrupole_spherical_to_cartesian(*molecular_quadrupole)

    return molecular_quadrupole
