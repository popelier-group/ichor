from typing import Optional

from ichor.atoms import Atoms
from ichor.files.file import File, FileContents
from ichor.files.geometry.atom_data import AtomData

class GeometryFile(File):
    """ A class which is inherited from any file which contains the full geometry
    of the molecule/system. These geometries can be used to calculate connectivity
    and ALF. Files such as .xyz, .gjf, .wfn have the full geometry of the system
    (i.e. they have x,y,z coordinates for every atom in the system, but each file
    might have different units!). We can use any of these files to determine the
    connectivity or calculate the ALF.
    
    :param path: a path to a file
    """

    atoms: Optional[Atoms]

    def __init__(self, path, atoms: Atoms = FileContents):
        super().__init__(path)
        self.atoms = atoms

    @property
    def features(self):
        return self.atoms.features

    @property
    def atom_names(self):
        return [atom.name for atom in self.atoms]

    def __getitem__(self, item):
        """ Returns all the data associated with an atom name"""
        if isinstance(item, str) and item in self.atoms.names:
            return AtomData(self.atoms[item], properties=self)
        return super().__getitem__(item)
