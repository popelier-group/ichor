import numpy as np
from ichor.core.calculators.spherical_to_cartesian_calculator import (
    spherical_to_cartesian,
)


def alf_features_to_coordinates(features: np.ndarray) -> np.ndarray:
    """Converts a given n_points x n_features matrix of features to cartesian coordinates of shape
    n_points x n_atoms x 3. Note cartesian coordinates are in Bohr as features
    are usually calculated in Bohr!

    :param features: a numpy array of shape n_points x n_features

    .. note::
        The distances in the features are in Bohr, so the resulting Cartesian
        coordinates will also be in Bohr. You will need to multiply by
        bohr2ang (in ichor.core.constants) to convert to Cartesian coordinates in Angstroms.
    """

    if features.ndim == 1:
        features = np.expand_dims(features, axis=0)

    all_points = []  # 3d array
    one_point = []  # 2d array

    for row in features:  # iterate over rows, which are individual points

        # origin and x-axis and xy-plane atoms
        one_point.append([0.0, 0.0, 0.0])
        one_point.append([row[0], 0.0, 0.0])
        # only have xy plane atom and others if molecule is not diatomic
        if len(row) > 1:
            one_point.append(
                spherical_to_cartesian(row[1], np.pi / 2, row[2])
            )  # theta is always pi/2 because it is in the xy plane

            # all other atoms
            for i in range(3, features.shape[-1], 3):
                r = row[i]
                theta = row[i + 1]
                phi = row[i + 2]
                one_point.append(spherical_to_cartesian(r, theta, phi))

        all_points.append(one_point)
        one_point = []

    return np.array(all_points)
