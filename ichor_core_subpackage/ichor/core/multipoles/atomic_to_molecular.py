import numpy as np
from ichor.core.atoms import Atoms
from ichor.core.common.constants import coulombbohr_to_debye
from ichor.core.files import INTs
from ichor.core.multipoles.dipole import atomic_contribution_to_molecular_dipole


def recover_molecular_dipole(
    atoms: Atoms, ints_dir: INTs, atoms_in_angstroms=True, convert_to_debye=True
):
    """
    Reads in a geometry (atoms) and _atomicfiles directory containing AIMAll output files
    and calculates the molecular dipole moment of the system (in spherical coordinates)
    from the AIMAll atomic multipole moments.

    .. note::
        Assumes atomic multipole moment units are atomic units (Coulomb Bohr) because this is what AIMAll gives.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an INTs file instance, which wraps around an AIMAll output directory
    :param atoms_in_angstroms: Whether the Atom instance coordinates are in Bohr or Angstroms
        , defaults to True (meaning coordinates are in Angstroms)
    :param convert_to_debye: Whether or not to convert the final result to Debye, default to True.
        This converts from atomic units to Debye.
    :returns: A numpy array containing the molecular dipole moment. Note that it is in spherical coordinates.
    """

    # make sure we are in Bohr
    if atoms_in_angstroms:
        atoms = atoms.to_bohr()

    molecular_dipole = np.array(3)

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

    return molecular_dipole
