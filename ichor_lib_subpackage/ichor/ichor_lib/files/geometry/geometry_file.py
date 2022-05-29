from ichor.ichor_lib.files.file import File
from ichor.ichor_lib.files.geometry.atom_data import AtomData
from typing import Union, List
from pathlib import Path
from abc import ABC
from ichor.ichor_lib.atoms.calculators import AtomSequenceALFCalculator
from ichor.ichor_lib.atoms.calculators import ALFFeatureCalculator

class GeometryFile(File, ABC):
    """ A class which is inherited from any file which contains the full geometry
    of the molecule/system. These geometries can be used to calculate connectivity
    and ALF. Files such as .xyz, .gjf, .wfn have the full geometry of the system
    (i.e. they have x,y,z coordinates for every atom in the system, but each file
    might have different units!). We can use any of these files to determine the
    connectivity or calculate the ALF.
    
    :param path: a path to a file
    """

    def __init__(self, path: Union[Path, str]):
        super().__init__(path)

    @property
    def coordinates(self) -> "np.ndarray":
        return self.atoms.coordinates

    @property
    def atom_names(self) -> List[str]:
        return [atom.name for atom in self.atoms]

    def features(self, alf_calculator = AtomSequenceALFCalculator, features_calculator = ALFFeatureCalculator) -> "np.ndarray":
        return self.atoms.features(alf_calculator, features_calculator)

    def __getitem__(self, item):
        """ Returns all the data associated with an atom name"""
        if isinstance(item, str) and item in self.atoms.names:
            return AtomData(self.atoms[item], properties=self)
        return super().__getitem__(item)
