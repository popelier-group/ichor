import itertools as it

import numpy as np

from ichor.atoms.calculators.feature_calculator.feature_calculator import \
    FeatureCalculator
from ichor.constants import ang2bohr
from ichor.units import AtomicDistance

feature_unit = AtomicDistance.Bohr


class ALFFeatureCalculator(FeatureCalculator):
    _alf = None

    @classmethod
    def calculate_alf(cls, atom) -> list:
        """Returns the Atomic Local Frame (ALF) of the specified atom. The ALF consists of 3 Atom instances,
        the central atom, the x-axis atom, and the xy-plane atom. These are later used to calculate the C rotation
        matrix and features.

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom for which we want to calculate the ALF.

        Returns:
            :type: `list`
                A list of Atom instances of length 3. The 0th element of the list is the central atom Atom instance,
                the 1st element is the x-axis Atom instance, and the 2nd element is the xy-plane Atom instance.
        """

        def _priority_by_mass(atoms) -> float:
            """Returns the sum of masses of a list of Atom instances

            Args:
                :param: `atoms` a list of Atom instances:

            Returns:
                :type: `float`
                The sum of the masses of the Atom instances that were given in the input `atoms`.
            """
            return sum([a.mass for a in atoms])

        def _get_priority(atom, level):
            """Returns the priority of atoms on a given level."""
            atoms = [atom]
            for _ in range(level):
                atoms_to_add = []
                for a in atoms:
                    for bonded_atom in a.bonded_atoms:
                        if bonded_atom not in atoms:
                            atoms_to_add.append(bonded_atom)

                atoms += atoms_to_add

            return _priority_by_mass(atoms)

        def _max_priority(atoms: list):
            """Returns the Atom instance that has the highest priority in the given list.

             Args:
                :param: `atoms` a list of Atom instances:

            Returns:
                :type: `Atom` instance
                    The atom instance with the highest priority by mass.
            """
            prev_priorities = []
            level = it.count(0)
            while True:
                next_lvl = next(level)  # starts at 0
                priorities = [_get_priority(atom, next_lvl) for atom in atoms]
                if (
                    priorities.count(max(priorities)) == 1
                    or prev_priorities == priorities
                ):
                    break
                else:
                    prev_priorities = priorities
            return atoms[priorities.index(max(priorities))]

        def _calculate_alf(atom) -> list:
            """Returns a list consisting of the x-axis and xy-plane Atom instances, which
            correspond to the atoms of first and second highest priorty as determined by the
            Cahn-Ingold-Prelog rules."""
            alf = [atom]
            # we need to get 2 atoms - one for x-axis and one for xy-plane
            for _ in range(2):
                # make a list of atoms to which the central atom is bonded to that are not in alf
                queue = [a for a in atom.bonded_atoms if a not in alf]
                # if queue is empty, then we add the bonded atoms of the atoms that the atom of interest is connected to
                if len(queue) == 0:
                    queue = list(
                        it.chain.from_iterable(
                            a.bonded_atoms for a in atom.bonded_atoms
                        )
                    )
                    # again remove atoms if they are already in alf
                    queue = [a for a in queue if a not in alf]
                max_priority_atom = _max_priority(queue)
                alf.append(max_priority_atom)
            return alf

        # add the atom of interest to the x_axis and xy_plane atoms, thus this returns a list of 3 Atom instances.
        if cls._alf is None:
            cls._alf = [None for _ in range(len(atom.parent))]
        if cls._alf[atom.index - 1] is None:
            cls._alf[atom.index - 1] = [
                a.index - 1 for a in _calculate_alf(atom)
            ]
        return cls._alf[atom.index - 1]

    @classmethod
    def calculate_x_axis_atom(cls, atom):
        """Returns the Atom instance that is used as the x-axis of the ALF

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom which we want to calculate the ALF for.

        Returns:
            :type: `Atom` instance
                The Atom instance which corresponds to the x-axis atom
        """
        # print(cls.calculate_alf(atom))
        # print(cls._alf)
        # quit()
        return atom.parent[cls.calculate_alf(atom)[1]]

    @classmethod
    def calculate_xy_plane_atom(cls, atom):
        """Returns the Atom instance that is used as the x-axis of the ALF

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom which we want to calculate the ALF for.

        Returns:
            :type: `Atom` instance
                The Atom instance which corresponds to the xy-plane atom
        """
        return atom.parent[cls.calculate_alf(atom)[2]]

    @classmethod
    def calculate_c_matrix(cls, atom) -> np.ndarray:
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

        x_axis_atom = cls.calculate_x_axis_atom(atom)
        xy_plane_atom = cls.calculate_xy_plane_atom(atom)

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
    def calculate_features(cls, atom):
        """Calculates the features for the given central atom.

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom for which we want to calculate the C rotation matrix.

        Returns:
            :type: `np.ndarray`
                A 1D numpy array of shape 3N-6, where N is the number of atoms in the system which `atom` is a part of.
        """
        feature_array = np.empty(3 * len(atom.parent) - 6)

        # Feature calculation assumes units are in angstroms
        atom.to_angstroms()
        atom.parent.to_angstroms()
        unit_conversion = (
            1.0 if feature_unit is AtomicDistance.Angstroms else ang2bohr
        )

        x_axis_atom = cls.calculate_x_axis_atom(atom)
        xy_plane_atom = cls.calculate_xy_plane_atom(atom)

        x_axis_vect = unit_conversion * (
            x_axis_atom.coordinates - atom.coordinates
        )
        xy_plane_vect = unit_conversion * (
            xy_plane_atom.coordinates - atom.coordinates
        )

        x_bond_norm = np.linalg.norm(x_axis_vect)
        xy_bond_norm = np.linalg.norm(xy_plane_vect)

        angle = np.arccos(
            np.dot(x_axis_vect, xy_plane_vect.T) / (x_bond_norm * xy_bond_norm)
        )

        feature_array[0] = x_bond_norm
        feature_array[1] = xy_bond_norm
        feature_array[2] = angle

        c_matrix = cls.calculate_c_matrix(atom)

        # the rest of the atoms are described as 3 features each: distance(r), polar angle(theta), and azimuthal angle(phi) - physics convention
        # theta is between 0 and pi (not cyclic), phi is between 0 and 2pi (cyclic)

        if len(atom._parent) > 3:
            i_feat = 3
            for jatom in atom._parent:
                if (
                    (jatom is x_axis_atom)
                    or (jatom is xy_plane_atom)
                    or (jatom is atom)
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
