import itertools as it
from typing import List, Optional, Union
import numpy as np
from ichor.ichor_lib.common.functools import classproperty
from pathlib import Path
import warnings
from ichor.ichor_lib.atoms.calculators.alf_calculator import ALFCalculator

class CahnIngoldPrelogALFCalculator(ALFCalculator):
    
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