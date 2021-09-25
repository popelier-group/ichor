from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd

from ichor.analysis.get_models import number_of_models_in_dir
from ichor.analysis.predictions import get_true_predicted
from ichor.models import Models, ModelsResult
from ichor.points import PointsDirectory

# todo: add plots


def calculate_rmse(models_location: Path, validation_set_location: Path):
    """
    Calculates rmse errors for a given directory containing model files and a given validation set directory.

    :param models_location: The directory where models are located.
    :type models_location: Path
    :param validation_set_location: The directory where the validation set is located.
    :type validation_set_location: Path
    """
    if number_of_models_in_dir(models_location) > 0:
        models = [Models(models_location)]
    else:
        models = [
            Models(modeldir)
            for modeldir in models_location.iterdir()
            if modeldir.is_dir()
        ]

    validation_set = PointsDirectory(validation_set_location)

    _calculate_rmse(models, validation_set)


def _calculate_rmse(
    models: Union[Models, List[Models]], validation_set: PointsDirectory
):
    true_values = {}
    predicted_values = {}
    if isinstance(models, Models):
        models = [models]

    for model in models:
        true, predicted = get_true_predicted(model, validation_set)

        # keys: integers corresponding to number of training points, values: a nested dictionary which first layer being the atom name and second being property name
        true_values[model.ntrain] = true
        predicted_values[model.ntrain] = predicted

    write_to_excel(true_values, predicted_values)


def write_to_excel(
    true_values: Dict[int, ModelsResult],
    predicted_values: Dict[int, ModelsResult],
    output: Path = "rmse_new_implementation.xlsx",
):
    from collections import defaultdict
    # not sure if OrderedDict needed for python 3.6, but use it for now
    from collections import OrderedDict
    # sort the models by the training points
    true_values = OrderedDict(sorted(true_values.items()))
    predicted_values = OrderedDict(sorted(predicted_values.items()))

    with pd.ExcelWriter(output) as writer:

        all_rmse_errors = defaultdict(lambda: defaultdict(float))

        # loop over all models which have different numbers of training points
        for ntrain, true, predicted in zip(
            true_values.keys(), true_values.values(), predicted_values.values()
        ):

            sheet_name = f"{ntrain} points"
            true = true.T
            predicted = predicted.T
            rmse_data = {}

            errors_to_write = []
            # loop over all types (eg. iqa, q00, etc.)
            for type_ in true.keys():

                type_errors = []

                # loop over all atoms (eg. C1, H2, O3, etc.)
                for atom in true[type_].keys():

                    # make true and predicted columns
                    rmse_data[f"{atom}_{type_} True"] = true[type_][atom]
                    rmse_data[f"{atom}_{type_} Predicted"] = predicted[type_][atom]

                    # calculate mean absolute error (MAE)
                    abs_error = np.abs(true[type_][atom] - predicted[type_][atom])

                    # calculate MAE and append to errors row to be written below the last row of the df
                    mean_absolute_error = np.mean(abs_error).item()
                    errors_to_write.append(mean_absolute_error)
                    # also write this error to dictionary which will be used to make an MAE sheet
                    all_rmse_errors[f"{atom}_{type_}"][ntrain] = mean_absolute_error

                    # add Absolute Error Column
                    rmse_data[f"{atom}_{type_} absError"] = abs_error


                    type_errors += [abs_error]

                # after looping thorugh all atoms, we can sum up all the errors to make a total error column for every property
                # make the list into a 2D numpy array and sum over the rows, which are the errors for each atom
                total_error = np.sum(np.array(type_errors), axis=0)
                rmse_data[f"{type_} Total absError"] = total_error

                # calculate total MAE and append to errors row to be written below the last row of the df
                total_mean_absolute_error = np.mean(total_error).item()
                errors_to_write.append(total_mean_absolute_error)
                # also write this error to dictionary which will be used to make an RMSE sheet
                all_rmse_errors[f"total_{type_}"][ntrain] = total_mean_absolute_error

            df = pd.DataFrame(rmse_data)
            df.to_excel(writer, sheet_name=sheet_name)

            # get the number of rows. Since excel starts counting from 1, this number will be the next empty row where we can write MAE
            n_rows = df.shape[0]

            # write out the MAE row for every third column.
            col_idx = 0
            writer.sheets[sheet_name].write(n_rows+1, col_idx, "MAE")
            col_idx += 3
            for error in errors_to_write[:-1]:
                writer.sheets[sheet_name].write(n_rows+1, col_idx, error)
                col_idx += 3
            # subtract two columns as we need to write out the Total absError MAE, but that should be written right next to the previous MAE
            col_idx -= 2
            writer.sheets[sheet_name].write(n_rows+1, col_idx, errors_to_write[-1])

        # make the sheet that only contains MAE information
        df = pd.DataFrame(all_rmse_errors)
        df.to_excel(writer, sheet_name="MAE")
        writer.sheets["MAE"].write(0, 0, "n_train")