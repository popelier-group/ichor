import numpy as np
from ichor.core.units import AtomicDistance
from ichor.core.atoms.calculators import ALF, calculate_c_matrix
from ichor.core.constants import ang2bohr

def calculate_alf_features(atom, alf: ALF, feature_unit: AtomicDistance = AtomicDistance.Bohr) -> np.ndarray:

    """Calculates the features for the given central atom.

    Args:
        :param: `cls` the class ALFFeatureCalculator:
        :param: `atom` an instance of the `Atom` class:
            This atom is the central atom for which we want to calculate the C rotation matrix.

    Returns:
        :type: `np.ndarray`
            A 1D numpy array of shape 3N-6, where N is the number of atoms in the system which `atom` is a part of.
    """

    if len(atom.parent) == 2:
        feature_array = np.empty(
            1
        )  # if only 2 atoms are in parent, there are only 2 atoms in the system so there is only 1 feature - distance.
    elif len(atom.parent) > 2:
        feature_array = np.empty(
            3 * len(atom.parent) - 6
        )  # for systems with more than 2 atoms, we have 3N-6 features
    else:
        raise ValueError(
            "atom.parent needs to have more than 1 atom in order to calculate features."
        )

    # Convert to angstroms to make sure units are in angstroms
    # For not features are calculated in bohr, so the unit_conversion is ang2bohr
    # TODO: this is not ideal because it changes the instance coordinates directly, so it might cause bugs
    atom.to_angstroms()
    atom.parent.to_angstroms()
    unit_conversion = (
        1.0 if feature_unit is AtomicDistance.Angstroms else ang2bohr
    )

    x_axis_atom_instance = atom.parent[alf.x_axis_idx]
    x_axis_vect = unit_conversion * (
        x_axis_atom_instance.coordinates - atom.coordinates
    )
    x_bond_norm = np.linalg.norm(x_axis_vect)

    # return array if only 2 atoms, i.e. only 1 feature needed
    if len(atom.parent) == 2:
        feature_array[0] = x_bond_norm
        return feature_array

    # this code is only needed if atom.parent is more than 2 atoms (so it has 3N-6 features)
    xy_plane_atom_instance = atom.parent[alf.xy_plane_idx]

    xy_plane_vect = unit_conversion * (
        xy_plane_atom_instance.coordinates - atom.coordinates
    )

    xy_bond_norm = np.linalg.norm(xy_plane_vect)

    angle = np.arccos(
        np.dot(x_axis_vect, xy_plane_vect.T) / (x_bond_norm * xy_bond_norm)
    )

    feature_array[0] = x_bond_norm
    feature_array[1] = xy_bond_norm
    feature_array[2] = angle

    c_matrix = calculate_c_matrix(atom)

    # the rest of the atoms are described as 3 features each: distance(r), polar angle(theta), and azimuthal angle(phi) - physics convention
    # theta is between 0 and pi (not cyclic), phi is between -pi and pi (cyclic)

    if len(atom._parent) > 3:
        i_feat = 3
        for jatom in atom._parent:
            if (
                (jatom.name == x_axis_atom_instance.name)
                or (jatom.name == xy_plane_atom_instance.name)
                or (jatom.name == atom.name)
            ):
                continue

            r_vect = unit_conversion * (
                jatom.coordinates - atom.coordinates
            )
            r_vect_norm = np.linalg.norm(r_vect)
            feature_array[i_feat] = r_vect_norm

            i_feat += 1

            zeta = np.dot(c_matrix, r_vect)
            feature_array[i_feat] = np.arccos(zeta[2] / r_vect_norm)

            i_feat += 1

            feature_array[i_feat] = np.arctan2(zeta[1], zeta[0])

            i_feat += 1

    return feature_array
