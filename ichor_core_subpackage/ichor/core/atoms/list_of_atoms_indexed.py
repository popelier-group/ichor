
from ichor.core.atoms import ListOfAtoms

class ListOfAtomsIndexed(ListOfAtoms):
    def __init__(self, parent, sl):
        self.__dict__ = parent.__dict__.copy()
        self._is_list_of_atoms_slice = True
        list.__init__(self)

        for i in sl:
            self.append(list.__getitem__(parent, i))