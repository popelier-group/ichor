from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

# from ichor.core.atoms.atom import Atom
#
# from ichor.core.atoms.atoms import Atoms
from ichor.core.common.functools import classproperty

# class ALF:
#     def __init__(self, origin: int, x_axis: int, xy_plane: int):
#         self.origin_idx = origin
#         self.x_axis_idx = x_axis
#         self.xy_plane_idx = xy_plane
#
#     def get_x_axis_atom(self, atoms: Atoms) -> Atom:
#         return atoms[self.x_axis_idx]
#
#     def get_xy_plane_atom(self, atoms: Atoms) -> Atom:
#         return atoms[self.xy_plane_idx]


class ALFCalculator:  # (ABC):
    """Abstract base class for calculating atomic local frame of atoms in a system.
    The atomic local frame can then be used to calculate features (the features are
    different depending on the local frame that is chosen).
    """

    # @abstractmethod
    @classmethod
    def calculate_alf(cls):
        pass

    # @abstractmethod
    @classmethod
    def _calculate_x_axis_atom(cls, atom):
        pass

    # @abstractmethod
    @classmethod
    def _calculate_xy_plane_atom(cls, atom):
        pass

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

        if isinstance(alf, list):
            from ichor.core.atoms.atom import Atom

            if isinstance(alf[1], int):
                return atom.parent[alf[1] - 1]
            elif isinstance(alf[1], Atom):
                return atom.parent[alf[1].i]
        elif isinstance(alf, np.ndarray):
            return atom.parent[alf[1]]

        return cls._calculate_x_axis_atom(atom)

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

        if isinstance(alf, list):

            if isinstance(alf[2], int):
                return atom.parent[alf[2] - 1]
            # assume that alf contains list of Atom instances otherwise
            else:
                return atom.parent[alf[2].i]
        elif isinstance(alf, np.ndarray):
            return atom.parent[alf[2]]

        return cls._calculate_xy_plane_atom(atom)

    @classproperty
    def alf(cls):
        """Returns a dictionary of system_hash:alf."""
        if not hasattr(cls, "_reference_alf"):
            cls._reference_alf = ALFCalculator.get_alfs()
        return cls._reference_alf

    @classmethod
    def get_alfs(cls, reference_file: Path = None):
        """Returns a dictionary as the system has as keys and alf for all atoms (a list of list)
        as values.

        :param reference_file: A file containing the ALF references. It has the following structure:
            O1,H2,H3 [[0,1,2],[1,0,2],[2,0,1]]
            C1,H2,O3,H4,H5,H6 [[0,2,1],[1,0,2],[2,0,1],[3,0,2],[4,0,2],[5,2,1]]
        """

        from ast import literal_eval
        from collections import defaultdict

        alf = defaultdict(list)

        if reference_file is not None and reference_file.exists():
            with open(reference_file, "r") as alf_reference_file:
                for line in alf_reference_file:
                    system_hash, total_alf = line.split(maxsplit=1)
                    # read in atomic local frame and convert to list of list of int.
                    alf[system_hash] = literal_eval(total_alf)

        return alf
