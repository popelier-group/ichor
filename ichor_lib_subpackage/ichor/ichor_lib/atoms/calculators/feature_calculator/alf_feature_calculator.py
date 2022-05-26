import itertools as it
from typing import List, Optional, Union

import numpy as np

from ichor.ichor_lib.atoms.calculators.feature_calculator.feature_calculator import \
    FeatureCalculator
from ichor.ichor_lib.constants import ang2bohr
from ichor.ichor_lib.units import AtomicDistance
from ichor.ichor_lib.common.functools import classproperty
from pathlib import Path
import warnings

feature_unit = AtomicDistance.Bohr
class ALFCalculationError(Exception):
    pass

class ALFFeatureCalculator(FeatureCalculator):

    @classproperty
    def _alf(self):
        """ Returns a dictionary of system_hash:alf."""
        if not hasattr(self, "_reference_alf"):
            self._reference_alf = ALFFeatureCalculator.get_alfs()
        return self._reference_alf

    @classmethod
    def get_alfs(cls, reference_file: Path = None):
        """ Returns a dictionary as the system has as keys and alf for all atoms (a list of list)
        as values.
        
        :param reference_file: A file containing the ALF references. It has the following structure:
            O1,H2,H3 [[0,1,2],[1,0,2],[2,0,1]]
            C1,H2,O3,H4,H5,H6 [[0,2,1],[1,0,2],[2,0,1],[3,0,2],[4,0,2],[5,2,1]]
        """

        from ast import literal_eval

        alf = {}

        if reference_file.exists():
            with open(reference_file, "r") as alf_reference_file:
                for line in alf_reference_file:
                    system_hash, total_alf = line.split(maxsplit=1)
                    # read in atomic local frame and convert to list of list of int.
                    alf[system_hash] = literal_eval(total_alf)

        return alf
    
    @classmethod
    def calculate_alf(cls, atom: "Atom") -> list:
        """Returns the Atomic Local Frame (ALF) of the specified atom, note that it is 0-indexed. The ALF consists of 3 Atom instances,
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

        def _priority_by_mass(atoms: List["Atom"]) -> float:
            """Returns the sum of masses of a list of Atom instances

            Args:
                :param: `atoms` a list of Atom instances:

            Returns:
                :type: `float`
                The sum of the masses of the Atom instances that were given in the input `atoms`.
            """
            return sum([a.mass for a in atoms])

        def _get_priority(atom: "Atom", level: int):
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

        def _max_priority(atoms: List["Atom"]):
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

        def _calculate_alf(atom) -> List["Atom"]:
            """Returns a list consisting of the x-axis and xy-plane Atom instances, which
            correspond to the atoms of first and second highest priorty as determined by the
            Cahn-Ingold-Prelog rules."""
            alf = [atom]
            # we need to get 2 atoms - one for x-axis and one for xy-plane. If the molecule is 2d (like HCl), then we only need 1 atom.
            n_atoms_in_alf = 2 if len(atom.parent) > 2 else 1
            for _ in range(n_atoms_in_alf):
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

        # since the systems we are working on are not isomers we assume that the connectivity of the atoms remains the same
        # if connectivity changes but the atoms remain the same (i.e. it is a different configuration), then this code might not work
        # we use a dictionary where we store a key = hash (a string with all the atom names) and value = a list of alfs for the whole system
        system_hash = atom.parent.hash
        if system_hash not in cls._alf.keys():
            warnings.warn("The atomic local frame has not been read in from the reference file. \
                The computed ALF might be different. If you want to make sure the same ALF is used, \
                then specify an alf reference file.")
            # make an empty list to fill with the alfs for the system
            cls._alf[system_hash] = []
            # calculate the alf for every atom in the system and add to the list above
            for atm in atom.parent:
                alf = _calculate_alf(atm)
                cls._alf[system_hash].append([a.i for a in alf])

        # return a list of the index (starts at 0 because we use this alf to index lists) of central atom, the x_axis and xy_plane atoms
        return cls._alf[system_hash][atom.i]

    @classmethod
    def calculate_x_axis_atom(
        cls,
        atom: "Atom",
        alf: Optional[Union[List[int], List["Atom"], np.ndarray]] = None,
    ) -> "Atom":
        """Returns the Atom instance that is used as the x-axis of the ALF

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom which we want to calculate the ALF for.

        Returns:
            :type: `Atom` instance
                The Atom instance which corresponds to the x-axis atom
        """
        if alf is None:
            return atom.parent[cls.calculate_alf(atom)[1]]
        elif isinstance(alf, list):
            from ichor.ichor_lib.atoms.atom import Atom

            if isinstance(alf[1], int):
                return atom.parent[alf[1] - 1]
            elif isinstance(alf[1], Atom):
                return atom.parent[alf[1].i]
        elif isinstance(alf, np.ndarray):
            return atom.parent[alf[1]]

    @classmethod
    def calculate_xy_plane_atom(
        cls,
        atom: "Atom",
        alf: Optional[Union[List[int], List["Atom"], np.ndarray]] = None,
    ) -> "Atom":
        """Returns the Atom instance that is used as the x-axis of the ALF

        Args:
            :param: `cls` the class ALFFeatureCalculator:
            :param: `atom` an instance of the `Atom` class:
                This atom is the central atom which we want to calculate the ALF for.

        Returns:
            :type: `Atom` instance
                The Atom instance which corresponds to the xy-plane atom
        """
        if alf is None:
            return atom.parent[cls.calculate_alf(atom)[2]]
        elif isinstance(alf, list):
            from ichor.ichor_lib.atoms.atom import Atom

            if isinstance(alf[2], int):
                return atom.parent[alf[2] - 1]
            elif isinstance(alf[2], Atom):
                return atom.parent[alf[2].i]
        elif isinstance(alf, np.ndarray):
            return atom.parent[alf[2]]

    @classmethod
    def calculate_c_matrix(
        cls,
        atom: "Atom",
        alf: Optional[Union[List[int], List["Atom"], np.ndarray]] = None,
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
