from typing import Callable, List, Union

import numpy as np
from ichor.core.atoms import ListOfAtoms
from ichor.core.atoms.alf import ALF


class AtomView(ListOfAtoms):
    """
    Class used to index a ListOfAtoms instance by an atom name (eg. C1, H2, etc.). This allows
    a user to get information (such as coordinates or features) for one atom.

    :param parent: An instance of a class that subclasses from ListOfAtoms
    :param atom: A string representing the name of an atom, e.g. C1, H2, etc.
    """

    def __init__(self, parent, atom):
        list.__init__(self)
        self._atom = atom
        # do not copy the self.__dict__ as some of the methods will not work in ListOfAtomsAtomView
        self._is_atom_view = True
        self._super = parent

        # this usually iterates over Atoms instances that are stored instance and only adds the information for the
        # specified atom. Thus AtomView is essentially a list of Atom instances for only one atom
        # also iterates over PointDirectory instances because PointsDirectory subclasses from ListofAtoms
        for element in parent:
            a = element[atom]
            self.append(a)

    @property
    def atom_name(self):
        """Returns the name of the atom, e.g. 'C1', 'H2', etc."""
        return self._atom

    # this has to return the name of the atom in a list, so that other methods work correctly
    @property
    def atom_names(self):
        """Returns a list containing the name of the atom (so contains 1 element)"""
        return [self.atom_name]

    # this has to return the natoms in the original class instance so that methods work correctly
    # even though there is really only 1 atom in the AtomView object
    @property
    def natoms(self):
        """Returns the name of the atom, e.g. 'C1', 'H2', etc."""
        return self._super.natoms

    @property
    def type(self):
        """Returns the types of atoms in the atom view.
        Since only one atom type is present, it returns a list with one element"""
        return [self[0].type]

    def connectivity(self, connectivity_calculator: Callable):
        """Returns the alf calculated from the first Atom object inside the ListOfAtomsAtomView object"""
        # get the connectivity for the first Atom instance
        return connectivity_calculator(self[0].parent)[self[0].i]

    def alf(self, alf_calculator: Callable, *args, **kwargs):
        """Returns the alf calculated from the first Atom object inside the ListOfAtomsAtomView object"""
        return alf_calculator(self[0], *args, **kwargs)

    def C(self, alf: Union[ALF, List[int]]):
        """Returns the C matrix for every Atom instance in the ListOfAtomsAtomView.

        Thus, the shape is n_timesteps x 3 x 3
        """
        return np.array([atm.C(alf) for atm in self])

    def features(self, feature_calculator: Callable, *args, **kwargs) -> np.ndarray:
        """
        Return the ndarray of features for only one atom, given an alf for that atom.
        This is assumed to a 2D array of features for only one atom.

        :param alf: A list of integers or a numpy array corresponding to the alf of one atom
            The atom which the atom view is for.
        :return: The array has shape ``n_timesteps`` x ``n_features``.
        """

        return np.array(
            [atom.features(feature_calculator, *args, **kwargs) for atom in self]
        )
