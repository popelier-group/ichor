def calculate_alf_atom_sequence(atom: "Atom") -> "ALF":
    
    from ichor.core.atoms.alf import ALF

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
            x_axis_idx = atom.i - 2
        # if the first atom in sequence return the next index
        elif atom.i == 0:
            x_axis_idx = atom.i + 1
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
        elif atom.i == 0:
            xy_plane_idx = atom.i + 2
        # otherwise return the atom that is one away (next atom in sequence)
        else:
            xy_plane_idx = atom.i + 1

        return ALF(atom.i, x_axis_idx, xy_plane_idx)
