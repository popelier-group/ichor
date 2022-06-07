from ichor.core.atoms.calculators.alf_calculator import ALFCalculator

class AtomSequenceALFCalculator(ALFCalculator):

    """Calculates the ALF for every atom based on the sequence of how the atoms were read in
    from the geometry file (gjf, xyz, etc.). Because a trajectory should contain the same
    sequence of atoms for every timestep, this means this calculator should calculate
    the same atomic local frame atoms (the same x-axis and same xy-plane atom) for every
    geometry (this class does not depend on connectivity between atoms, just the sequence of
    the atoms in the geometry file).
    
    For the first atom in the sequence, the next two atoms are the x-axis and xy-plane atoms.
    For middle atoms, the previous atom and the next atoms are the x-axis and xy-plane atoms.
    For the last atom, the previous two atoms are the x-axis and xy-plane atoms.
    """

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

        system_hash = atom.parent.hash
        # calculate the alf for every atom in the system and add to the list above
        for atm in atom.parent:
            cls.alf[system_hash].append([atm.i, cls.calculate_x_axis_atom(atm), cls.calculate_xy_plane_atom(atm)])

        return [atom.i, cls.calculate_x_axis_atom(atm), cls.calculate_xy_plane_atom(atm)]

    @classmethod
    def _calculate_x_axis_atom(cls, atom):

        # if we have 3 atoms or more
        if len(atom.parent) > 2:
            # if the last atom in the sequence, return atom i that is two away
            if atom.i + 1 == len(atom.parent):
                return atom.i - 2
            # if the first atom in sequence return the next index
            elif atom.index == 0:
                return atom.i + 1
            # otherwise return the atom that is one away (previous atom in sequence)
            else:
                return atom.i - 1

        # if we only have 2 atoms, then we can only have 0 and 1 indices
        elif len(atom.parent) == 2:
            # if last atom, return 0 as x-axis
            if atom.i == 1:
                return 0
            # if first atom, then return 1 as x-axis
            else:
                return 1
        
    @classmethod
    def _calculate_xy_plane_atom(cls, atom):

        # if we have 3 atoms or more
        if len(atom.parent) > 2:
            # if the last atom in the sequence, return the previous i, as this is xy-plane atom 
            if atom.i + 1 == len(atom.parent):
                return atom.i - 1
            # if the first atom in sequence return the next next atom (2 away)
            elif atom.index == 0:
                return atom.i + 2
            # otherwise return the atom that is one away (next atom in sequence)
            else:
                return atom.i + 1