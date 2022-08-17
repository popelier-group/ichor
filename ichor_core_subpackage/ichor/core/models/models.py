import re
from functools import wraps
from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd
from ichor.core.atoms import Atoms, ListOfAtoms
from ichor.core.atoms import ALF
from ichor.core.common.sorting.natsort import ignore_alpha, natsorted
from ichor.core.common.str import get_digits
from ichor.core.files import Directory, HasAtoms
from ichor.core.common.types.itypes import F
from ichor.core.models.model import Model


class DimensionError(ValueError):
    pass


def x_to_features(func: F) -> F:
    """Used as a decorator to convert an incoming set of test points `x` to features because we need to know the test point features in
    order to make predictions."""

    @wraps(func)
    def wrapper(self, x, *args, **kwargs):
        features = self.get_features_dict(x)
        return func(self, features, *args, **kwargs)

    return wrapper


class Models(Directory, list):
    """A class which wraps around a directory containing models made by FEREBUS or any other program used to make GP models. There are different
    models for iqa energy and each individual multipole moment. Aditionally, every atom in the system has its own set of models for iqa and
    multipole moments. These models can have different training input/output data if the models have been made with per-atom.
    """

    def __init__(self, path):
        list.__init__(self)
        Directory.__init__(self, path)

    def _parse(self) -> None:
        """Parse a directory and add any `.model` files to the `Models` instance"""
        for f in self:
            if f.suffix == Model.filetype:
                self.append(Model(f))

    def dirpattern(self, pattern):
        """A regex pattern used to find directories containing models."""
        return re.compile(rf"{pattern}\d+/")

    @classmethod
    def check_path(cls, path: Path) -> bool:
        if path.exists() and path.is_dir():
            for f in path.iterdir():
                if f.suffix == Model.filetype:
                    return True
        return False

    @property
    def atom_names(self) -> List[str]:
        """Returns a list of atom names (such as O1, H2, H3, etc.) for which models were made"""
        return list(
            set(natsorted([model.atom for model in self], key=ignore_alpha))
        )

    @property
    def types(self) -> List[str]:
        """Returns a list of types (such as q00, q10, iqa, etc.) for which models were made"""
        return list({model.type for model in self})

    @property
    def alf(self) -> List[ALF]:
        """Returns the alf taken straight from each model file e.g. [[1, 2, 3], [2, 1, 3], [3, 1, 2]]"""
        return sorted([model.alf for model in self])

    @property
    def ialf(self) -> np.ndarray:
        """Returns the zero index alf from each model file as a numpy array e.g. [[0, 1, 2], [1, 0, 2], [2, 0, 1]]

        .. note::
            Sorting by the first integer in elements of the list will give a list like this [[0,...], [1,....], [2,....]].
            Before that the list could look like [[2,...], [0,....], [1,....]] (because the models could be unordered)
            which would mess up the alf for atoms.
        """
        return np.array(
            sorted([model.ialf for model in self], key=lambda x: x[0])
        )

    @property
    def ialf_dict(self) -> Dict[str, np.ndarray]:
        """Returns the zero index alf from each model file as a dictionary e.g. {'O1': [0, 1, 2], 'H2': [1, 0, 2], 'H3': [2, 0, 1]}"""
        return {model.atom: model.ialf for model in self}

    @property
    def ntrain(self) -> int:
        """Returns the maximum number of training points that were used for a model in this `Models` instance."""
        return max(model.ntrain for model in self)

    @property
    def system(self) -> str:
        """Returns the name of the system for which models were made."""
        return self[0].system

    @x_to_features
    def predict(self, x_test) -> pd.DataFrame:
        # todo: update docs
        """Returns dictionary of DataFrame({"atom": {"property": [values]}})"""
        return pd.DataFrame(
            {
                atom: {
                    model.type: model.predict(features) for model in self[atom]
                }
                for atom, features in x_test.items()
            }
        )

    @x_to_features
    def variance(self, x_test) -> pd.DataFrame:
        return pd.DataFrame(
            {
                atom: {
                    model.type: model.variance(features)
                    for model in self[atom]
                }
                for atom, features in x_test.items()
            }
        )

    def get_features_dict(
        self, test_x: Union[Atoms, ListOfAtoms, np.ndarray, HasAtoms, dict]
    ) -> Dict[str, np.ndarray]:
        """Returns a dictionary containing the atom names as keys and an np.ndarray of features as values.

        :param test_x: An object that contains features (or coordinates that can be converted into features), such as `Atoms`, `ListOfAtoms`, `np.ndarray`, `dict`
        :return: A dictionary containing the atom names as keys and an np.ndarray of features as values
        """

        if isinstance(test_x, Atoms):
            return self._features_from_atoms(test_x)
        elif isinstance(test_x, ListOfAtoms):
            return self._features_from_list_of_atoms(test_x)
        elif isinstance(test_x, HasAtoms):
            return self._features_from_geometry_file(test_x)
        elif isinstance(test_x, np.ndarray):
            return self._features_from_array(test_x)
        elif isinstance(test_x, dict):
            return test_x
        raise TypeError(f"Cannot predict values from type '{type(test_x)}'")

    def _features_from_atoms(self, atoms: Atoms) -> Dict[str, np.ndarray]:
        """Returns a dictionary containing atom name as key and atom features for values."""
        return {
            atom.name: atom.alf_features(alf=self.ialf_dict[atom])
            for atom in atoms
        }

    def _features_from_list_of_atoms(
        self, x_test: ListOfAtoms
    ) -> Dict[str, np.ndarray]:
        return {
            atom: x_test[atom].alf_features(alf=self.alf)
            for atom in self.atom_names
            if atom in x_test.atom_names
        }

    def _features_from_geometry_file(
        self, x_test: HasAtoms
    ) -> Dict[str, np.ndarray]:
        return {
            atom: x_test.atoms[atom].alf_features(alf=self.alf)
            for atom in self.atom_names
            if atom in x_test.atom_names
        }

    def _features_from_array(self, x_test: np.ndarray):
        if x_test.ndim == 2:
            return {
                atom: x_test[get_digits(atom) - 1][np.newaxis, :]
                for atom in self.atom_names
            }
        elif x_test.ndim == 3:
            return {atom: x_test[i] for i, atom in enumerate(self.atom_names)}
        else:
            raise DimensionError(
                f"'x_test' is of incorrect dimensions ({x_test.ndim}) 'x_test' must be either 2D or 3D"
            )

    def __getitem__(self, args):
        if isinstance(args, (str, tuple)):
            return ModelsView(self, args)
        elif isinstance(args, int):
            return list.__getitem__(self, args)

    def __iter__(self):
        return (
            Directory.__iter__(self) if len(self) == 0 else list.__iter__(self)
        )


class ModelsView(Models):
    def __init__(self, models, *args):
        Directory.__init__(self, models.path)
        list.__init__(self)
        for arg in args:
            for model in models:
                if arg in (model.atom, model.type):
                    self.append(model)

    def __getattr__(self, item):
        if len(self) == 1:
            return getattr(self[0], item)
