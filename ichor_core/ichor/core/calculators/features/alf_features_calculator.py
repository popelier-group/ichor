from typing import Dict, List, Union

import numpy as np
from ichor.core.calculators.alf import get_atom_alf
from ichor.core.calculators.c_matrix_calculator import calculate_c_matrix
from ichor.core.common.constants import ang2bohr
from ichor.core.common.units import AtomicDistance


default_distance_unit: AtomicDistance = AtomicDistance.Bohr


def calculate_alf_features(
    atom: "ichor.core.atoms.Atom",  # noqa F821
    # need to be like this because importing classes leads to circular import issues
    alf: Union[
        "ichor.core.atoms.ALF",  # noqa F821
        List["ichor.core.atoms.ALF"],  # noqa F821
        List[List[int]],
        Dict[str, "ichor.core.atoms.ALF"],  # noqa F821
    ],  # noqa F821
    distance_unit: AtomicDistance = default_distance_unit,
) -> np.ndarray:
    """Calculates the features for the given central atom.

    Args:
        :param atom: an instance of the `Atom` class:
            This atom is the central atom for which we want to calculate the C rotation matrix.
        :param alf: A callable or instance of `ALF` that is used to
            calculate the atomic local frame for the atom. This atomic local frame then defines the
            features which are going to be calculated. If no ALF is passed by user,
            then the default way of calculating ALF is used.
        :param distance_unit: The distance units to use for the calculated distances
            which are part of the features. The default distance is Bohr.

    Returns:
        :type: `np.ndarray`
            A 1D numpy array of shape 3N-6, where N is the number of atoms
            in the system which `atom` is a part of. If there are only two atoms,
            then there is only 1 feature (the distance between the atoms).
    """

    alf = get_atom_alf(atom, alf)

    # if only 2 atoms are in parent, there are only 2 atoms
    # in the system so there is only 1 feature - distance.
    if len(atom.parent) == 2:
        feature_array = np.empty(1)
    elif len(atom.parent) > 2:
        feature_array = np.empty(
            3 * len(atom.parent) - 6
        )  # for systems with more than 2 atoms, we have 3N-6 features
    else:
        raise ValueError(
            "atom.parent needs to have more than 1 atom in order to calculate features."
        )

    # Convert to angstroms to make sure units are in angstroms to begin with
    # to_angstroms creates new instances which we use here to calculate features.
    # the atom outside of the function scope should remain the same as before
    atom = atom.to_angstroms()
    atom.parent = atom.parent.to_angstroms()

    unit_conversion = 1.0 if distance_unit is AtomicDistance.Angstroms else ang2bohr

    x_axis_atom_instance = atom.parent[alf.x_axis_idx]
    x_axis_vect = unit_conversion * (
        x_axis_atom_instance.coordinates - atom.coordinates
    )
    x_bond_norm = np.linalg.norm(x_axis_vect)

    # return array if only 2 atoms, i.e. only 1 feature needed
    if len(atom.parent) == 2:
        # feature_array[0] = 1.0 / x_bond_norm
        feature_array[0] = x_bond_norm
        return feature_array

    # this code is only needed if atom.parent is more than 2 atoms (so it has 3N-6 features)
    xy_plane_atom_instance = atom.parent[alf.xy_plane_idx]

    xy_plane_vect = unit_conversion * (
        xy_plane_atom_instance.coordinates - atom.coordinates
    )

    xy_bond_norm = np.linalg.norm(xy_plane_vect)

    # angle = np.arccos(
    #    np.dot(x_axis_vect, xy_plane_vect.T) / (x_bond_norm * xy_bond_norm)
    # )

    cos_chi = np.dot(x_axis_vect, xy_plane_vect.T) / (x_bond_norm * xy_bond_norm)

    # feature_array[0] = 1.0 / x_bond_norm
    # feature_array[1] = 1.0 / xy_bond_norm
    feature_array[0] = x_bond_norm
    feature_array[1] = xy_bond_norm
    feature_array[2] = cos_chi

    c_matrix = calculate_c_matrix(atom, alf)

    # the rest of the atoms are described as 3 features each:
    # distance(r), polar angle(theta), and azimuthal angle(phi) - physics convention
    # theta is between 0 and pi (not cyclic), phi is between -pi and pi (cyclic)

    if len(atom._parent) > 3:
        i_feat = 3
        for jatom in atom._parent:
            if jatom.name in [
                x_axis_atom_instance.name,
                xy_plane_atom_instance.name,
                atom.name,
            ]:
                continue

            r_vect = unit_conversion * (jatom.coordinates - atom.coordinates)
            r_vect_norm = np.linalg.norm(r_vect)
            # feature_array[i_feat] = 1.0 / r_vect_norm
            feature_array[i_feat] = r_vect_norm

            i_feat += 1

            zeta = np.dot(c_matrix, r_vect)
            # TODO: is few geometries zeta[2] / r_vect_norm can be evaluated as +-1.0000000001 or someting close
            # which is outside of the range of arccos
            # clipping zeta[2] / r_vect_norm between -1.0 and 1.0 solves the problem
            z2_rvect_clipped = np.clip(zeta[2] / r_vect_norm, -1.0, 1.0)

            feature_array[i_feat] = z2_rvect_clipped

            i_feat += 1

            phi = np.arctan2(zeta[1], zeta[0])

            feature_array[i_feat] = phi

            i_feat += 1

    return feature_array
