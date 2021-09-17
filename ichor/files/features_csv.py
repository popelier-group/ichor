from typing import List

import numpy as np
import pandas as pd

from ichor.atoms.atom import Atom
from ichor.atoms.atoms import Atoms
from ichor.files import Trajectory


def read_features_csv(
    csv_file: "Path", n_features: int, header=None, index_col=None
):
    """Read in a csv file and give back an array corresponding to features. It assumes that the
    features start from the first column (column after the index column).

    :param csv_file: Path to the csv file
    :param n_features: Integer corresponding to the number of features (3N-6)
    :param header: Whether the first line of the csv file contains the names of the columns. Default is None. Set to 0 to use the 0th row.
    :param index_col: Whether a column should be used as the index column. Default is None, so no column used. Set to 0 to use 0th column.
    """

    values = pd.read_csv(csv_file, header=header, index_col=index_col).values
    return values[:, :n_features]


def spherical_to_cartesian(r, theta, phi):
    """
    Spherical to cartesian transformation, where r ∈ [0, ∞), θ ∈ [0, π], φ ∈ [-π, π).
        x = rsinθcosϕ
        y = rsinθsinϕ
        z = rcosθ
    """
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(theta)
    return [x, y, z]


def features_to_coordinates(features: np.ndarray) -> np.ndarray:
    """Converts a given n_points x n_features matrix of features to cartesian coordinates of shape
    n_points x n_atoms x 3

    :param features: a numpy array of shape n_points x n_features
    """

    all_points = []  # 3d array
    one_point = []  # 2d array

    for row in features:  # iterate over rows, which are individual points

        # origin and x-axis and xy-plane atoms
        one_point.append([0, 0, 0])
        one_point.append([row[0], 0, 0])
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


def features_csv_to_trajectory(
    csv_file: "Path",
    n_features: int,
    atom_types: List[str],
    header=None,
    index_col=None,
) -> Trajectory:

    """Takes in a csv file containing features and convert it to a `Trajectory` object.
    It assumes that the features start from the first column (column after the index column, if one exists).

    :param csv_file: Path to the csv file
    :param n_features: Integer corresponding to the number of features (3N-6)
    :param atom_types: A list of strings corresponding to the atom elements (C, O, H, etc.). This has to be ordered the same way
        as atoms corresponding to the features.
    :param header: Whether the first line of the csv file contains the names of the columns. Default is None. Set to 0 to use the 0th row.
    :param index_col: Whether a column should be used as the index column. Default is None, so no column used. Set to 0 to use 0th column.
    """

    features_array = read_features_csv(
        csv_file=csv_file,
        n_features=n_features,
        header=header,
        index_col=index_col,
    )
    xyz_array = features_to_coordinates(features_array)

    trajectory = Trajectory()

    for geometry in xyz_array:

        atoms = Atoms()

        for ty, atom_coord in zip(atom_types, geometry):

            atoms.add(Atom(ty, atom_coord[0], atom_coord[1], atom_coord[2]))

        trajectory.add(atoms)

    return trajectory
