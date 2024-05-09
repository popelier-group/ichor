def calculate_alf_atom_sequence(
    atom: "ichor.core.atoms.Atom",  # noqa F821
) -> "ichor.core.atoms.ALF":  # noqa F821

    from ichor.core.atoms.alf import ALF

    """
    Calculates the ALF for every atom based on the sequence of how the atoms were read in
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

    # x-axis and xy-plane atoms calculations (0-indexed)

    # if we have 3 atoms or more, i.e. we have both x-axis and xy-plane atoms
    if len(atom.parent) > 2:

        if atom.i + 1 == len(atom.parent):
            # if the last atom in the sequence, then x-axis atom is two away
            x_axis_idx = atom.i - 2
            # and the xy-plane atom is one less
            xy_plane_idx = atom.i - 1

        elif atom.i == 0:
            # if the first atom in sequence, x axis atom is 1 away
            x_axis_idx = atom.i + 1
            # are the xy-plane atom is 2 indices away
            xy_plane_idx = atom.i + 2

        else:
            # otherwise return the atom that is one away before the current atom for x-axis
            x_axis_idx = atom.i - 1
            # and atom that is one away in sequence after current atom for xy-plane
            xy_plane_idx = atom.i + 1

    # if we only have 2 atoms, then we can only have 0 and 1 indices
    elif len(atom.parent) == 2:
        xy_plane_idx = None
        # if last atom, then 0 atom is x-axis
        if atom.i == 1:
            x_axis_idx = 0
        # otherwise then return 1 as x-axis
        else:
            x_axis_idx = 1

    return ALF(atom.i, x_axis_idx, xy_plane_idx)
