from ichor.core.calculators.connectivity import default_connectivity_calculator


# TODO: use connectivity here instead of connectivity calculator.
# typing annotations need to be like this because of circular imports
def calculate_alf_cahn_ingold_prelog(
    atom: "ichor.core.atoms.Atom",  # noqa F821
    connectivity_calculator=default_connectivity_calculator,
) -> "ichor.core.atoms.ALF":  # noqa F821

    from ichor.core.atoms.alf import ALF

    """Returns the Atomic Local Frame (ALF) of the specified atom,
    note that it is 0-indexed. The ALF consists of 3 Atom instances,
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

    import itertools as it
    from typing import List

    def _priority_by_mass(atoms: List["Atom"]) -> float:  # noqa F821
        """Returns the sum of masses of a list of Atom instances

        Args:
            :param: `atoms` a list of Atom instances:

        Returns:
            :type: `float`
            The sum of the masses of the Atom instances that were given in the input `atoms`.
        """
        return sum(a.mass for a in atoms)

    def _get_priority(atom: "Atom", level: int):  # noqa F821
        """Returns the priority of atoms on a given level."""
        atoms = [atom]
        for _ in range(level):
            atoms_to_add = []
            for a in atoms:
                atoms_to_add.extend(
                    bonded_atom
                    for bonded_atom in a.bonded_atoms(connectivity_calculator)
                    if bonded_atom not in atoms
                )

            atoms += atoms_to_add

        return _priority_by_mass(atoms)

    def _max_priority(atoms: List["Atom"]):  # noqa F821
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
            if priorities.count(max(priorities)) == 1 or prev_priorities == priorities:
                break
            else:
                prev_priorities = priorities
        return atoms[priorities.index(max(priorities))]

    def _calculate_alf(atom) -> List["Atom"]:  # noqa F821
        """Returns a list consisting of the x-axis and xy-plane Atom instances, which
        correspond to the atoms of first and second highest priorty as determined by the
        Cahn-Ingold-Prelog rules."""
        alf = [atom]
        # we need to get 2 atoms - one for x-axis and one for xy-plane.
        # If the molecule is 2d (like HCl), then we only need 1 atom.
        n_atoms_in_alf = 2 if len(atom.parent) > 2 else 1
        if len(atom.parent) == 1:
            raise ValueError(
                "ALF cannot be calculated because there is only 1 atom. Two or more atoms are necessary."
            )

        for _ in range(n_atoms_in_alf):
            # make a list of atoms to which the central atom is bonded to that are not in alf
            queue = [
                a for a in atom.bonded_atoms(connectivity_calculator) if a not in alf
            ]
            # if queue is empty, then we add the bonded atoms of the atoms that the atom of interest is connected to
            if not queue:
                queue = list(
                    it.chain.from_iterable(
                        a.bonded_atoms(connectivity_calculator)
                        for a in atom.bonded_atoms(connectivity_calculator)
                    )
                )
                # again remove atoms if they are already in alf
                queue = [a for a in queue if a not in alf]
            max_priority_atom = _max_priority(queue)
            alf.append(max_priority_atom)
        return alf

    # return a list of the index (starts at 0 because we use this alf to index lists)
    # of central atom, the x_axis and xy_plane atoms
    return ALF(*[a.i for a in _calculate_alf(atom)])
