class ALF(list):
    """ Atomic Local Frame used for one atom. Atomic local frame consists of central atom index,
    x-axis atom index, xy-plane atom index. These indices are 0-indexed. The xy-plane atom
    might not exist if there are only 2 atoms, so default for it is None."""
    def __init__(self, origin: int, x_axis: int, xy_plane: int = None):
        super().__init__(origin, x_axis, xy_plane)

    @property
    def origin_idx(self):
        return self[0]

    @property
    def x_axis_idx(self):
        return self[1]

    @property
    def xy_plane_idx(self):
        return self[2]

def calculate_atom_sequence_alf(atom: "Atom") -> ALF:

    """Calculates the ALF for every atom based on the sequence of how the atoms were read in
    from the geometry file (gjf, xyz, etc.). Because a trajectory should contain the same
    sequence of atoms for every timestep, this means this calculator should calculate
    the same atomic local frame atoms (the same x-axis and same xy-plane atom) for every
    geometry (this class does not depend on connectivity between atoms, just the sequence of
    the atoms in the geometry file).

    For the first atom in the sequence, the next two atoms are the x-axis and xy-plane atoms.
    For middle atoms, the previous atom and the next atoms are the x-axis and xy-plane atoms.
    For the last atom, the previous two atoms are the x-axis and xy-plane atoms.

    Args:
        :param: `cls` the class ALFFeatureCalculator:
        :param: `atom` an instance of the `Atom` class:
            This atom is the central atom for which we want to calculate the ALF.

    Returns:
        :type: `list`
            A list of Atom instances of length 3. The 0th element of the list is the central atom Atom instance,
            the 1st element is the x-axis Atom instance, and the 2nd element is the xy-plane Atom instance.
    """

    # X-axis atom index calculation (0-indexed)
    # if we have 3 atoms or more
    if len(atom.parent) > 2:
        # if the last atom in the sequence, return atom i that is two away
        if atom.i + 1 == len(atom.parent):
            x_axis_idx =  atom.i - 2
        # if the first atom in sequence return the next index
        elif atom.index == 0:
            x_axis_idx =  atom.i + 1
        # otherwise return the atom that is one away (previous atom in sequence)
        else:
            x_axis_idx = atom.i - 1

    # if we only have 2 atoms, then we can only have 0 and 1 indices
    elif len(atom.parent) == 2:
        # if last atom, return 0 as x-axis
        if atom.i == 1:
            x_axis_idx = 0
        # if first atom, then return 1 as x-axis
        else:
            x_axis_idx = 1

    # XY-plane atom index calculation (0-indexed)
    xy_plane_idx = None
    # if we have 3 atoms or more
    if len(atom.parent) > 2:
        # if the last atom in the sequence, return the previous i, as this is xy-plane atom
        if atom.i + 1 == len(atom.parent):
            xy_plane_idx = atom.i - 1
        # if the first atom in sequence return the next next atom (2 away)
        elif atom.index == 0:
            xy_plane_idx = atom.i + 2
        # otherwise return the atom that is one away (next atom in sequence)
        else:
            xy_plane_idx = atom.i + 1

        return ALF(atom.i, x_axis_idx, xy_plane_idx)

def calculate_cahn_ingold_prelog_alf(atom: "Atom") -> ALF:
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

    import itertools as it
    from typing import List

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

    # return a list of the index (starts at 0 because we use this alf to index lists) of central atom, the x_axis and xy_plane atoms
    return ALF(*_calculate_alf(atom))
