from ichor.models import Models, ModelsResult
from ichor.analysis.predictions import get_true_predicted
from typing import Union, List, Dict
from ichor.analysis.get_models import number_of_models_in_dir

from ichor.points import PointsDirectory

from pathlib import Path
import pandas as pd
import numpy as np


# todo: add plots


def calculate_rmse(models_location: Path, validation_set_location: Path):
    if number_of_models_in_dir(models_location) > 0:
        models = [Models(models_location)]
    else:
        models = [Models(modeldir) for modeldir in models_location.iterdir() if modeldir.is_dir()]

    validation_set = PointsDirectory(validation_set_location)

    _calculate_rmse(models, validation_set)


def _calculate_rmse(models: Union[Models, List[Models]], validation_set: PointsDirectory):
    true_values = {}
    predicted_values = {}
    if isinstance(models, Models):
        models = [models]

    for model in models:
        true, predicted = get_true_predicted(model, validation_set)
        true_values[model.ntrain] = true
        predicted_values[model.ntrain] = predicted

    write_to_excel(true_values, predicted_values)


def write_to_excel(true_values: Dict[int, ModelsResult], predicted_values: Dict[int, ModelsResult], output: Path = 'rmse.xlsx'):
    with pd.ExcelWriter(output) as writer:
        rmse_data = {}
        for ntrain, true, predicted in zip(true_values.keys(), true_values.values(), predicted_values.values()):
            rmse_data[ntrain] = {}
            sheet_name = f"{ntrain} points"
            true = true.T
            predicted = predicted.T
            df = pd.DataFrame()
            columns = 0
            for type_ in true.keys():
                type_errors = []
                for atom in true[type_].keys():
                    df[f"{atom}_{type_} True"] = np.append(true[type_][atom], np.NaN)
                    df[f"{atom}_{type_} Predicted"] = np.append(predicted[type_][atom], np.NaN)
                    error = np.abs(true[type_][atom] - predicted[type_][atom])
                    mean_error = np.mean(error)
                    df[f"{atom}_{type_} Error"] = np.append(error, mean_error)
                    rmse_data[ntrain][f"{atom}_{type_}"] = mean_error
                    columns += 3
                    type_errors += [error]
                total_error = np.sum(np.array(type_errors), axis=0)
                mean_total_error = np.mean(total_error)
                df[f"{type_} Total Error"] = np.append(total_error, mean_total_error)
                rmse_data[ntrain][f"total_{type_}"] = mean_total_error
                columns += 1

            df.rename(index={len(df)-1: "RMSE"}, inplace=True)
            df.to_excel(writer, sheet_name=sheet_name)

        rmse_df = pd.DataFrame(rmse_data).T
        rmse_df.to_excel(writer, sheet_name="RMSE")
