import numpy as np
from typing import Union, Optional
from ichor.core.atoms.calculators.alf import (
    ALF,
    ALFCalculatorFunction,
    default_alf_calculator,
)


def calculate_c_matrix(
    atom: "Atom",
    alf: Optional[Union[ALF, ALFCalculatorFunction]] = None,
) -> np.ndarray:

    """Retruns the C rotation matrix that relates the global Cartesian coordinates to the ALF Cartesian Coordinates.
    See https://pubs.acs.org/doi/pdf/10.1021/ct500565g , Section 3.3 for the derivations. This matrix has 3 unit
    vectors.

    Args:
        :param: `cls` the class ALFFeatureCalculator:
        :param: `atom` an instance of the `Atom` class:
            This atom is the central atom for which we want to calculate the C rotation matrix.

    Returns:
        :type: `np.ndarray`
            A 3x3 numpy array which is the C rotation matrix.
    """

    if alf is None:
        alf = default_alf_calculator

    if not isinstance(alf, ALF):
        alf = alf(atom)

    c_matrix = np.empty((3, 3))

    x_axis_atom_instance = atom.parent[alf.x_axis_idx]
    xy_plane_atom_instance = atom.parent[alf.xy_plane_idx]

    # first row
    row1 = (
        x_axis_atom_instance.coordinates - atom.coordinates
    ) / np.linalg.norm(x_axis_atom_instance.coordinates - atom.coordinates)

    # second row
    x_axis_diff = x_axis_atom_instance.coordinates - atom.coordinates
    xy_plane_diff = xy_plane_atom_instance.coordinates - atom.coordinates

    sigma_fflux = -np.dot(x_axis_diff, xy_plane_diff) / np.dot(
        x_axis_diff, x_axis_diff
    )

    y_vec = sigma_fflux * x_axis_diff + xy_plane_diff

    row2 = y_vec / np.linalg.norm(y_vec)

    # third row
    row3 = np.cross(row1, row2)

    c_matrix[0, :] = row1
    c_matrix[1, :] = row2
    c_matrix[2, :] = row3

    return c_matrix
