import numpy as np
from ichor.core.calculators.alf import get_atom_alf


def calculate_c_matrix(
    atom: "Atom",  # noqa F821
    alf: "ALF",  # noqa F821
) -> np.ndarray:

    """Returns the C rotation matrix that relates the global Cartesian coordinates to the ALF Cartesian Coordinates.
    See https://pubs.acs.org/doi/pdf/10.1021/ct500565g , Section 3.3 for the derivations. This matrix has 3 unit
    vectors.

    :param: ``atom`` an instance of the ``Atom`` class:
        This atom is the central atom for which we want to calculate the C rotation matrix.
    :param alf: An Atomic Local Frame instance for the particular atom.

    :return: A 3x3 numpy array which is the C rotation matrix.
    """

    alf = get_atom_alf(atom, alf)

    c_matrix = np.empty((3, 3))

    if atom.parent.natoms > 2:

        x_axis_atom_instance = atom.parent[alf.x_axis_idx]
        xy_plane_atom_instance = atom.parent[alf.xy_plane_idx]

        x_axis_diff = x_axis_atom_instance.coordinates - atom.coordinates

        # first row
        row1 = (x_axis_diff) / np.linalg.norm(x_axis_diff)

        # second row
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

    # if we only have 2 atoms, e.g HCl
    else:

        x_axis_atom_instance = atom.parent[alf.x_axis_idx]
        x_axis_diff = x_axis_atom_instance.coordinates - atom.coordinates

        # there is no xy-plane atom, so we make a dummy atom
        # that is somewhere away from the central atom and x-axis atom
        xy_plane_diff = (
            atom.coordinates
            + x_axis_atom_instance.coordinates
            + np.array([1.0, 1.0, 1.0])
        ) - atom.coordinates

        # first row
        row1 = (x_axis_atom_instance.coordinates - atom.coordinates) / np.linalg.norm(
            x_axis_atom_instance.coordinates - atom.coordinates
        )

        # second row
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
