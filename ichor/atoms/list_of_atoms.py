from typing import Union


class ListOfAtoms(list):
    """Used to focus only on how one atom moves in a trajectory, so the usercan do something
     like trajectory['C1'] where trajectory is an instance of class Trajectory. This way the
    user can also do trajectory['C1'].features, trajectory['C1'].coordinates, etc."""
    def __init__(self):
        list.__init__(self)

    @property
    def atoms(self):
        """Returns the names of the atoms that are in the first timestep."""
        return [atom.name for atom in self[0]] if len(self) > 0 else []

    def iteratoms(self):
        for atom in self.atoms:
            yield self[atom]

    def __getitem__(self, item: Union[int, str]):
        """Used when indexing a trajectory by an integer or string"""
        if isinstance(item, int):
            return super().__getitem__(item)
        elif isinstance(item, str):

            class AtomView(self.__class__):
                def __init__(self, parent, atom):
                    self.__dict__ = parent.__dict__.copy()
                    list.__init__(self)
                    self._atom = atom
                    self._is_atom_view = True
                    for element in parent:
                        self.append(element[atom])

                @property
                def atoms(self):
                    return [self._atom]

                def __getattr__(self, item):
                    try:
                        return getattr(self[0], item)
                    except (AttributeError, IndexError):
                        raise AttributeError(
                            f"'{self.__class__.__name__}' has no attribute '{item}'"
                        )

            if hasattr(self, "_is_atom_view"):
                return self

            return AtomView(self, item)
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )
