from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd

from ichor.analysis.get_models import number_of_models_in_dir
from ichor.analysis.predictions import get_true_predicted
from ichor.models import Models, ModelsResult
from ichor.points import PointsDirectory

def calculate_rmse(models_location: Path, validation_set_location: Path, **kwargs):
    """
    Calculates rmse errors for a given directory containing model files and a given validation set directory. Also, writes the data to
    an excel file.

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

def make_rmse_chart_settings(local_kwargs: dict):
    """ Takes in a dictionary of key word arguments that were passed into the `write_to_excel` function. Then, this function
    constructs dictionaries with parameter values to be passed to xlsx writer to configure graph settings.
    
    :param local_kwargs: A dictionary containing key word arguments that are parsed to construct the xlsx-writer graph settings
    """

    from collections import defaultdict

    # make a dictionary with default values of dictionaries
    x_axis_settings = defaultdict(dict)
    y_axis_settings = defaultdict(dict)

    # x-axis settings
    x_axis_settings["name"] = local_kwargs["x_axis_name"]
    x_axis_settings["major_gridlines"]["visible"] = local_kwargs["x_major_gridlines_visible"]
    x_axis_settings["minor_gridlines"]["visible"] = local_kwargs["x_minor_gridlines_visible"]
    x_axis_settings["major_gridlines"]["line"] = {"width": local_kwargs["x_axis_major_gridline_width"], "color": local_kwargs["x_axis_major_gridline_color"]}
    if local_kwargs["x_log_scale"]:
        x_axis_settings["log_base"] = 10

    # y_axis_settings
    y_axis_settings["name"] = local_kwargs["error_type"].upper()
    y_axis_settings["major_gridlines"]["visible"] = local_kwargs["y_major_gridlines_visible"]
    y_axis_settings["minor_gridlines"]["visible"] = local_kwargs["y_minor_gridlines_visible"]
    x_axis_settings["major_gridlines"]["line"] = {"width": local_kwargs["y_axis_major_gridline_width"], "color": local_kwargs["y_axis_major_gridline_color"]}

    return x_axis_settings, y_axis_settings

def calculate_error(data: np.array, error_type: str):
    """ Calculates error for the data, given the error_type.
    
    :param data: A one dimensional numpy array which contains the (absolute) difference between true and predicted values for a property.
    :param error_type: The error type to calculate, either `mae` or `rmse`.
    """

    error_type = error_type.lower()

    if error_type == "mae":
        return np.mean(data).item()
    elif error_type == "rmse":
        return np.sqrt(np.mean(data**2)).item()
    else:
        raise ValueError("error_type value can either be 'rmse' or 'mae'")

def write_to_excel(
    true_values: Dict[int, ModelsResult],
    predicted_values: Dict[int, ModelsResult],
    output_name: Path = "rmse.xlsx",
    error_type: Union["mae", "rmse"] = "rmse",
    only_every_nth_model: Union[int, None] = None,
    x_axis_name:str = "Number of Training Points",
    x_log_scale:bool = False,
    x_major_gridlines_visible:bool = True,
    x_minor_gridlines_visible:bool = False,
    x_axis_major_gridline_width:int = 0.75,
    x_axis_major_gridline_color:str = "#F2F2F2",
    y_major_gridlines_visible:bool = True,
    y_minor_gridlines_visible:bool = False,
    y_axis_major_gridline_width:int = 0.75,
    y_axis_major_gridline_color:str = "#BFBFBF",
    show_legend:bool = True,
    excel_style:int = 10
):
    """
    Writes out relevant information which is used to write rmse to an excel file. It will make a separate sheet for training set and a final
    sheet containing MAE/RMSE errors.

    :param true_values: a dictionary of key: number of training points, value: a ModelsResult instance
    :param predicted_values: a dictionary of key: number of training points, value: a ModelsResult instance
    :param error_type: The type of error to calculate. Either Mean Absolute Error (MAE) or Root Mean Squared Error (RMSE). Default is RMSE ("rmse").
    :param only_every_nth_model: Only write out every `nth` model to the excel file, where `n` is an integer. This is useful if you have a very large number of models and only
        want to write out a subset of them. Defaults to None which means every model is written out.
    :param output_name: The name of the excel file to be written out.
    :param x_axis_name: The title to be used for x-axis in the MAE/RMSE plot.
    :param x_log_scale: Whether to make x dimension log scaled. Default True.
    :param x_major_gridlines_visible: Whether to show major gridlines along x. Default True.
    :param x_minor_gridlines_visible: Whether to show minor gridlines along x. Default True.
    :param x_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param x_axis_major_gridline_color: Color to use for gridlines. Default is "#F2F2F2".
    :param y_major_gridlines_visible: Whether to show major gridlines along y. Default True.
    :param y_minor_gridlines_visible: Whether to show minor gridlines along y. Default False.
    :param y_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param y_axis_major_gridline_color: Color to use for gridlines. Default is "#BFBFBF".
    :param show_legend: Whether to show legend on the plot. Default False.
    :param excel_style: The style which excel uses for the plots. Default is 10, which is the default style used by excel.
    """

    from collections import defaultdict
    # not sure if OrderedDict needed for python 3.6, but use it for now
    from collections import OrderedDict
    from ichor.constants import ha_to_kj_mol
    from ichor.analysis.excel import num2col

    # use the key word arguments to construct the settings used for x and y axes
    x_axis_settings, y_axis_settings = make_rmse_chart_settings(locals())

    # sort the models by the number of training points
    true_values = OrderedDict(sorted(true_values.items()))
    predicted_values = OrderedDict(sorted(predicted_values.items()))
    dictionary_keys = list(true_values.keys())

    # todo: move this is the calculate_rmse function where you can do this before making predictions, right now it makes the predictions and then deletes.
    # leave every nth model, delete the other ones. This can come in useful if you have a lot of models and do not want to go though each one 
    if only_every_nth_model:
        for idx in range(len(dictionary_keys)):
            if not (idx % only_every_nth_model == 0):
                key_to_del = dictionary_keys[idx]
                del true_values[key_to_del]
                del predicted_values[key_to_del]

    with pd.ExcelWriter(output_name) as writer:
        workbook = writer.book

        # make a dictionary of dictionaries which is used to write out the final sheet containing MAE errors for each n training point model
        all_errors_dict = defaultdict(lambda: defaultdict(float))

        # loop over all models which have different numbers of training points
        for ntrain, true, predicted in zip(
            true_values.keys(), true_values.values(), predicted_values.values()
        ):

            sheet_name = f"{ntrain} points"
            true = true.T
            predicted = predicted.T

            # a dict that is made into a pandas df and written to a separate excel sheet for every model
            rmse_data = {}
            # contains the MAE errors to be written at the bottom of the each sheet
            errors_to_write = []

            # loop over all types (eg. iqa, q00, etc.)
            for type_ in true.keys():

                # a list containing all the MAE errors to be written on the last line of the sheet
                type_errors = []

                # loop over all atoms (eg. C1, H2, O3, etc.)
                for atom in true[type_].keys():

                    # make true and predicted columns
                    rmse_data[f"{atom}_{type_} True (Ha)"] = true[type_][atom]
                    rmse_data[f"{atom}_{type_} Predicted (Ha)"] = predicted[type_][atom]

                    # calculate absolute error column, make into kJ mol-1 if working with iqa energies
                    if type_ == "iqa":
                        abs_error = ha_to_kj_mol * np.abs(true[type_][atom] - predicted[type_][atom])
                    else:
                        abs_error = np.abs(true[type_][atom] - predicted[type_][atom])

                    # add Absolute Error Column to df
                    rmse_data[f"{atom}_{type_} absError (kJ mol-1)"] = abs_error
                    type_errors += [abs_error]

                    # calculate MAE/RMSE and append to errors row to be written below the last row of the df
                    error_estimator = calculate_error(abs_error, error_type)
                    errors_to_write.append(error_estimator)
                    # also write this error to dictionary which will be used to make the final sheet containing mae/rmse
                    all_errors_dict[f"{atom}_{type_} (kJ mol-1)"][ntrain] = error_estimator

                # after looping thorugh all atoms, we can sum up all the errors to make a total error column for one property
                # make the list into a 2D numpy array and sum over the rows, which are the errors for each atom (for one property)
                total_abs_error = np.sum(np.array(type_errors), axis=0)
                rmse_data[f"{type_} Total absError (kJ mol-1)"] = total_abs_error

                # calculate total MAE/RMSE and append to errors list that is written on the row below the written dataframe
                total_mean_absolute_error = calculate_error(total_abs_error, error_type)
                errors_to_write.append(total_mean_absolute_error)
                # also write this error to the dictionary which is used to make the final sheet containing mae/rmse
                all_errors_dict[f"total_{type_} (kJ mol-1)"][ntrain] = total_mean_absolute_error

            df = pd.DataFrame(rmse_data)
            df.to_excel(writer, sheet_name=sheet_name)

            # get the number of rows. Since excel starts counting from 1, this number will be the next empty row where we can write RMSE
            n_rows = df.shape[0]
            # write out the RMSE row for every third column.
            col_idx = 0
            writer.sheets[sheet_name].write(n_rows+1, col_idx, error_type)
            col_idx += 3
            for error in errors_to_write[:-1]:
                writer.sheets[sheet_name].write(n_rows+1, col_idx, error)
                col_idx += 3
            # subtract two columns as we need to write out the Total absError MAE, but that should be written right next to the previous RMSE
            col_idx -= 2
            writer.sheets[sheet_name].write(n_rows+1, col_idx, errors_to_write[-1])

        # make the sheet that only contains RMSE information, pandas df can accept a dictionary of dictionaries
        df = pd.DataFrame(all_errors_dict)
        df.to_excel(writer, sheet_name=error_type)
        writer.sheets[error_type].write(0, 0, "n_train")

        # RMSE plot for IQA energies
        rmse_plot1 = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        # add data to plot
        for col in df.columns:
            if ("iqa" in col.lower()):
                rmse_plot1.add_series(
                    {
                        "name": col,
                        "categories": [error_type, 1, 0, df.shape[0], 0],
                        "values": [error_type, 1, df.columns.get_loc(col)+1, df.shape[0], df.columns.get_loc(col)+1],
                        "line": {"width": 1.5},
                    }
                )
        # add the plot to the error_type sheet
        rmse_plot1.set_x_axis(x_axis_settings)
        rmse_plot1.set_y_axis(y_axis_settings)
        if not show_legend:
            rmse_plot1.set_legend({"position": "none"})
        rmse_plot1.set_style(excel_style) # default style of excel plots

        writer.sheets[error_type].insert_chart(f"{num2col(df.shape[1]+3)}2", rmse_plot1)

        # RMSE plot for multipoles
        rmse_plot2 = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        # add data to plot
        for col in df.columns:
            if not ("iqa" in col.lower()):
                rmse_plot2.add_series(
                    {
                        "name": col,
                        "categories": [error_type, 1, 0, df.shape[0], 0],
                        "values": [error_type, 1, df.columns.get_loc(col)+1, df.shape[0], df.columns.get_loc(col)+1],
                        "line": {"width": 1.5},
                    }
                )
        # add the plot to the error_type sheet
        rmse_plot2.set_x_axis(x_axis_settings)
        rmse_plot2.set_y_axis(y_axis_settings)
        if not show_legend:
            rmse_plot2.set_legend({"position": "none"})
        rmse_plot2.set_style(excel_style) # default style of excel plots

        writer.sheets[error_type].insert_chart(f"{num2col(df.shape[1]+3)}19", rmse_plot2)