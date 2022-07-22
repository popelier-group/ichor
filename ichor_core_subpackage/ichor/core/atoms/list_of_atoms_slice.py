
from ichor.core.atoms import ListOfAtoms

class ListOfAtomsSlice(ListOfAtoms):
    def __init__(self, parent, sl):
        self.__dict__ = parent.__dict__.copy()
        self._is_atom_slice = True
        list.__init__(self)

        # slicing out of range does not raise an error. This is by design in Python
        self.extend(list.__getitem__(parent, sl))