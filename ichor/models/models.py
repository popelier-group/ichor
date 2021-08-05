import re
from functools import wraps
from typing import Dict, Union

import numpy as np

from ichor.atoms import Atoms, ListOfAtoms
from ichor.common.sorting.natsort import ignore_alpha, natsorted
from ichor.files import Directory
from ichor.models.model import Model
from ichor.models.result import ModelsResult
from ichor.typing import F


class DimensionError(ValueError):
    pass


def x_to_features(func: F) -> F:
    @wraps(func)
    def wrapper(self, x, *args, **kwargs):
        features = self.get_features_dict(x)
        return func(self, features, *args, **kwargs)

    return wrapper


class Models(Directory, list):
    def __init__(self, path):
        list.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.suffix == Model.filetype:
                self.append(Model(f))

    @property
    def dirpattern(self):
        from ichor.globals import GLOBALS

        return re.compile(rf"{GLOBALS.SYSTEM_NAME}\d+/")

    def get_features_dict(self, x) -> Dict[str, np.ndarray]:
        if isinstance(x, Atoms):
            return self._features_from_atoms(x)
        elif isinstance(x, ListOfAtoms):
            if len(self) < len(x):
                return self._features_from_list_of_atoms_models(x)
            else:
                return self._features_from_list_of_atoms(x)
        elif isinstance(x, np.ndarray):
            return self._features_from_array(x)
        elif isinstance(x, dict):
            return x
        raise TypeError(f"Cannot predict values from type '{type(x)}'")

    def _features_from_atoms(self, x: Atoms) -> Dict[str, np.ndarray]:
        return {atom.name: atom.features for atom in x}

    def _features_from_list_of_atoms(
        self, x: ListOfAtoms
    ) -> Dict[str, np.ndarray]:
        return {atom.name: atom.features for atom in x.iteratoms()}

    def _features_from_list_of_atoms_models(
        self, x: ListOfAtoms
    ) -> Dict[str, np.ndarray]:
        return {
            atom: x[atom].features
            for atom in self.atoms
            if atom in x.atom_names
        }

    def _features_from_array(self, x: np.ndarray):
        if x.ndim == 2:
            return {atom: x for atom in self.atoms}
        elif x.ndim == 3:
            return {atom: x[i] for i, atom in enumerate(self.atoms)}
        else:
            raise DimensionError(
                f"'x' is of incorrect dimensions ({x.ndim}) 'x' must be either 2D or 3D"
            )

    @x_to_features
    def predict(self, x) -> Dict[str, Dict[str, np.ndarray]]:
        return ModelsResult(
            {
                atom: {
                    model.type: model.predict(features) for model in self[atom]
                }
                for atom, features in x.items()
            }
        )

    @x_to_features
    def variance(self, x) -> Dict[str, Dict[str, np.ndarray]]:
        return ModelsResult(
            {
                atom: {
                    model.type: model.variance(features)
                    for model in self[atom]
                }
                for atom, features in x.items()
            }
        )

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
        return natsorted(
            list({model.atom for model in self}), key=ignore_alpha
        )

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

    def __getattr__(self, item):
        if len(self) == 1:
            return getattr(self[0], item)
