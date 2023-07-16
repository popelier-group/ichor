from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from ichor.core.atoms import ListOfAtoms
from ichor.core.files import PointsDirectory
from ichor.core.models import Models


def get_predicted(
    models: Models,
    points: ListOfAtoms,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Returns the predicted values for a given ListOfAtoms given Models

    :param models: the models to use for predicting the values of points
    :param points: a ListOfAtoms containing geometries to predict
    :param atoms: optional list of atoms to predict the values of points for, defaults to all atoms in models
    :param types: optional list of property types, such as iqa, q00, etc.
        to predict the values of points for, defaults to all types in models
    :return: predictions of points given models as a ModelsResult
    """
    if atoms is None:
        atoms = models.atom_names
    if types is None:
        types = models.types

    predicted = {}
    for atom in atoms:
        predicted[atom] = {}
        for type_ in types:
            predicted[atom][type_] = models[atom][type_].predict(points).array()

    return pd.DataFrame(predicted)


def get_true(
    validation_set: PointsDirectory, atoms: List[str], types: List[str]
) -> pd.DataFrame:
    """
    Returns the true values for a given PointsDirectory as a ModelsResult

    :param validation_set: the PointsDirectory containing the true values
    :param atoms: List of atoms to get the true values for
    :param types: List of property types, such as iqa, q00, etc. to get the true values for
    :return: ModelsResult containing the true values requested from the validation set
    """
    true = {}
    for atom in atoms:
        true[atom] = {}
        for type_ in types:
            true[atom][type_] = np.array(getattr(validation_set[atom], type_))

    return pd.DataFrame(true)


def get_true_predicted(
    models: Models,
    validation_set: PointsDirectory,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns the true and predicted values of the given model and
        validation set for each of the specified atoms and types

    :param models: models to use for the predictions
    :param validation_set: validation set containing geometry data and true values
    :param atoms: optional list of atoms to predict, defaults to all atoms found in model_location
    :param types: optional list of types to predict, such as iqa, q00, etc.
        Defaults to all types found in model_location
    :return: ModelsResult for true and predicted values from the models and validation set provided
    """
    if atoms is None:
        atoms = models.atom_names
    if types is None:
        types = models.types

    true = get_true(validation_set, atoms, types)
    predicted = get_predicted(models, validation_set, atoms, types)

    return true, predicted
