import re
from typing import Dict, Union, List

import numpy as np

from ichor.atoms import Atoms, ListOfAtoms
from ichor.files import Directory, FileState
from ichor.models.model import Model


class DimensionError(ValueError):
    pass


class Models(Directory, list):
    def __init__(self, path):
        list.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.suffix == Model.filetype:
                self.append(Model(f))

    @property
    def dirpattern(self) -> re.Pattern:
        from ichor.globals import GLOBALS

        return re.compile(f"{GLOBALS.SYSTEM_NAME}\d+/")

    @property
    def atoms(self) -> List[str]:
        return list(set(model.atom for model in self))

    @property
    def types(self) -> List[str]:
        return list(set(model.type for model in self))

    def predict(
        self, x: Union[Atoms, np.ndarray]
    ) -> Dict[str, Dict[str, np.ndarray]]:
        if isinstance(x, Atoms):
            return self._predict_from_atoms(x)
        elif isinstance(x, ListOfAtoms):
            if len(self) < len(x):
                return self._predict_from_list_of_atoms_models(x)
            else:
                return self._predict_from_list_of_atoms(x)
        elif isinstance(x, np.ndarray):
            return self._predict_from_array(x)
        raise TypeError(f"Cannot predict values from type '{type(x)}'")

    def _predict_from_atoms(
        self, x: Atoms
    ) -> Dict[str, Dict[str, np.ndarray]]:
        return {
            atom.name: {
                model.type: model.predict(atom.features)
                for model in self[atom.name]
            }
            for atom in x
        }

    def _predict_from_list_of_atoms(
        self, x: ListOfAtoms
    ) -> Dict[str, Dict[str, np.ndarray]]:
        return {
            atom_list.name: {
                model.type: model.predict(atom_list.features)
                for model in self[atom_list.name]
            }
            for atom_list in x.iteratoms()
        }

    def _predict_from_list_of_atoms_models(
        self, x: ListOfAtoms
    ) -> Dict[str, Dict[str, np.ndarray]]:
        return {
            atom: {
                model.type: model.predict(x[atom].features)
                for model in self[atom]
            }
            for atom in self.atoms
        }

    def _predict_from_array(
        self, x: np.ndarray
    ) -> Dict[str, Dict[str, np.ndarray]]:
        if x.ndim == 2:
            return {
                atom: {
                    model.type: model.predict(x)
                    for model in self[atom]
                }
                for atom in self.atoms
            }
        elif x.ndim == 3:
            return {
                atom: {
                    model.type: model.predict(x[model.i])
                    for model in self[atom]
                }
                for atom, xi in zip(self.atoms, x)
            }
        else:
            raise DimensionError(f"'x' is of incorrect dimensions ({x.ndim}) 'x' must be either 2D or 3D")

    def __getitem__(self, args):
        if isinstance(args, (str, tuple)):
            return ModelsView(self, args)
        elif isinstance(args, int):
            return list.__getitem__(self, args)

    def __iter__(self):
        if len(self) == 0:
            return Directory.__iter__(self)
        else:
            return list.__iter__(self)

    @property
    def atoms(self):
        return list({model.atom for model in self})

    @property
    def types(self):
        return list({model.type for model in self})


class ModelsView(Models):
    def __init__(self, models, *args):
        Directory.__init__(self, models.path)
        list.__init__(self)
        for arg in args:
            for model in models:
                if arg in [model.atom, model.type]:
                    self.append(model)
