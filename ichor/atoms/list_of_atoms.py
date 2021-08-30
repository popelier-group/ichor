from typing import Union

import numpy as np


class ListOfAtoms(list):
    """Used to focus only on how one atom moves in a trajectory, so the user can do something
     like trajectory['C1'] where trajectory is an instance of class Trajectory. This way the
    user can also do trajectory['C1'].features, trajectory['C1'].coordinates, etc."""

    def __init__(self):
        list.__init__(self)

    @property
    def atom_names(self):
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        return self[0].atom_names if len(self) > 0 else []

    @property
    def features(self):
        # matt_todo: Not exactly sure how to document this one because it returns different things depending on size of array
        # if 3D array (so has timesteps, atoms, and features) then transpose to get atoms, timesteps, features?
        features = np.array([i.features for i in self])
        if features.ndim == 3:
            features = np.transpose(features, (1, 0, 2))
        return features

    def iteratoms(self):
        """ Returns a generator of the atoms."""
        for atom in self.atom_names:
            yield self[atom]

    def __getitem__(self, item: Union[int, str]):
        """Used when indexing a Trajectory instance by an integer or string"""
        if isinstance(item, (int, np.int64)):
            return super().__getitem__(item)
        elif isinstance(item, str):

            class AtomView(self.__class__):
                def __init__(self, parent, atom):
                    list.__init__(self)
                    self.__dict__ = parent.__dict__.copy()
                    self._atom = atom
                    self._is_atom_view = True
                    self._super = parent

                    for element in parent:
                        a = element[atom]
                        a._properties = element
                        self.append(a)

                @property
                def name(self):
                    return self._atom

                @property
                def atom_names(self):
                    return [self._atom]

            if hasattr(self, "_is_atom_view"):
                return self
            return AtomView(self, item)
            
        elif isinstance(item, slice):

            class AtomSlice(self.__class__):
                def __init__(self, parent, sl):
                    self.__dict__ = parent.__dict__.copy()
                    self._is_atom_slice = True
                    list.__init__(self)
                    setattr(parent, "get_slice", True)
                    self.extend(parent[sl])
                    delattr(parent, "get_slice")

            if hasattr(self, "get_slice"):
                return super().__getitem__(item)
            return AtomSlice(self, item)
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )
