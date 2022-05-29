from typing import List, Optional, Union
import numpy as np
from ichor.ichor_lib.atoms.calculators.feature_calculator.feature_calculator import \
    FeatureCalculator
from ichor.ichor_lib.constants import ang2bohr
from ichor.ichor_lib.units import AtomicDistance

feature_unit = AtomicDistance.Bohr
class ALFCalculationError(Exception):
    pass

class ALFFeatureCalculator(FeatureCalculator):

    @classmethod
    def calculate_c_matrix(
        cls,
        atom: "Atom",
        alf: Union[List[int], List["Atom"], np.ndarray],
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
        c_matrix = np.empty((3, 3))

        x_axis_atom = cls.calculate_x_axis_atom(atom, alf)
        xy_plane_atom = cls.calculate_xy_plane_atom(atom, alf)

        # first row
        row1 = (x_axis_atom.coordinates - atom.coordinates) / np.linalg.norm(
            x_axis_atom.coordinates - atom.coordinates
        )

        # second row
        x_axis_diff = x_axis_atom.coordinates - atom.coordinates
        xy_plane_diff = xy_plane_atom.coordinates - atom.coordinates

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

    @classmethod
    def calculate_features(
        cls,
        atom: "Atom",
        alf: Optional[Union[List[int], List["Atom"], np.ndarray]] = None,
    ):
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
            )  # most systems have more than 2 atoms
        else:
            raise ValueError(
                "atom.parent needs to have more than 1 atom in order to calculate features."
            )

        # Convert to angstroms to make sure units are in angstroms
        # For not features are calculated in bohr, so the unit_conversion is ang2bohr
        atom.to_angstroms()
        atom.parent.to_angstroms()
        unit_conversion = (
            1.0 if feature_unit is AtomicDistance.Angstroms else ang2bohr
        )

        x_axis_atom = cls.calculate_x_axis_atom(atom, alf)
        x_axis_vect = unit_conversion * (
            x_axis_atom.coordinates - atom.coordinates
        )
        x_bond_norm = np.linalg.norm(x_axis_vect)

        if len(atom.parent) == 2:

            feature_array[0] = x_bond_norm
            return feature_array

        # this code is only needed if atom.parent is more than 2 atoms (so it has 3N-6 features)
        xy_plane_atom = cls.calculate_xy_plane_atom(atom, alf)

        xy_plane_vect = unit_conversion * (
            xy_plane_atom.coordinates - atom.coordinates
        )

        xy_bond_norm = np.linalg.norm(xy_plane_vect)

        angle = np.arccos(
            np.dot(x_axis_vect, xy_plane_vect.T) / (x_bond_norm * xy_bond_norm)
        )

        feature_array[0] = x_bond_norm
        feature_array[1] = xy_bond_norm
        feature_array[2] = angle

        c_matrix = cls.calculate_c_matrix(atom)

        # the rest of the atoms are described as 3 features each: distance(r), polar angle(theta), and azimuthal angle(phi) - physics convention
        # theta is between 0 and pi (not cyclic), phi is between -pi and pi (cyclic)

        if len(atom._parent) > 3:
            i_feat = 3
            for jatom in atom._parent:
                if (
                    (jatom.name == x_axis_atom.name)
                    or (jatom.name == xy_plane_atom.name)
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
