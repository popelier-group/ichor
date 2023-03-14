from pathlib import Path
from typing import List, Optional, Dict, Union

import numpy as np
import pandas as pd
from ichor.core.common.excel import num2col
from ichor.core.analysis.predictions import get_true_predicted
from ichor.core.common.sorting.natsort import ignore_alpha, natsorted
from ichor.core.common.constants import ha_to_kj_mol
from ichor.core.files import PointsDirectory
from ichor.core.models import Models
from collections import defaultdict
from ichor.core.common.constants import multipole_names


def percentile(n: int) -> np.ndarray:
    return np.linspace(100 / n, 100, n)

def make_chart_settings(local_kwargs: dict):
    """Takes in a dictionary of key word arguments that were passed into the `write_to_excel` function. Then, this function
    constructs dictionaries with parameter values to be passed to xlsx writer to configure graph settings.

    :param local_kwargs: A dictionary containing key word arguments that are parsed to construct the xlsx-writer graph settings
    """

    from collections import defaultdict

    # make a dictionary with default values of dictionaries
    x_axis_settings = defaultdict(dict)
    y_axis_settings = defaultdict(dict)

    # x-axis settings
    x_axis_settings["name"] = local_kwargs["x_axis_name"]
    x_axis_settings["major_gridlines"]["visible"] = local_kwargs[
        "x_major_gridlines_visible"
    ]
    x_axis_settings["minor_gridlines"]["visible"] = local_kwargs[
        "x_minor_gridlines_visible"
    ]
    x_axis_settings["major_gridlines"]["line"] = {
        "width": local_kwargs["x_axis_major_gridline_width"],
        "color": local_kwargs["x_axis_major_gridline_color"],
    }
    if local_kwargs["x_log_scale"]:
        x_axis_settings["log_base"] = 10

    # y_axis_settings
    y_axis_settings["name"] = local_kwargs["y_axis_name"]
    y_axis_settings["min"] = local_kwargs["y_min"]
    y_axis_settings["max"] = local_kwargs["y_max"]
    y_axis_settings["major_gridlines"]["visible"] = local_kwargs[
        "y_major_gridlines_visible"
    ]
    y_axis_settings["minor_gridlines"]["visible"] = local_kwargs[
        "y_minor_gridlines_visible"
    ]
    x_axis_settings["major_gridlines"]["line"] = {
        "width": local_kwargs["y_axis_major_gridline_width"],
        "color": local_kwargs["y_axis_major_gridline_color"],
    }

    return x_axis_settings, y_axis_settings

def simplified_write_to_excel(
    total_dict: Dict[str, Dict[str, Dict[str, np.ndarray]]],
    output_name: Path = "s-curves.xlsx",
    x_axis_name: str = "Absolute Prediction Error",
    x_log_scale: bool = True,
    x_major_gridlines_visible: bool = True,
    x_minor_gridlines_visible: bool = True,
    x_axis_major_gridline_width: int = 0.75,
    x_axis_major_gridline_color: str = "#F2F2F2",
    y_axis_name: str = "%",
    y_min: int = 0,
    y_max: int = 100,
    y_major_gridlines_visible: bool = True,
    y_minor_gridlines_visible: bool = False,
    y_axis_major_gridline_width: int = 0.75,
    y_axis_major_gridline_color: str = "#BFBFBF",
    show_legend: bool = False,
    excel_style: int = 10,
    sort_keys: bool = True
):
    """
    Writes out relevant information which is used to make s-curves to an excel file. It will make a separate sheet for every atom (and property). It
    also makes a `Total` sheet for every property, which gives an idea how the predictions do overall for the whole system.

    :param total_dict: a dictionary containing key: property, val: inner_dict.
        inner_dict contains key: atom_name, val: inner_inner_dict.
        inner_inner_dict contains: key: (true, predicted or error), val: a 1D numpy array containing the corresponding values
    :param output_name: The name of the excel file to be written out.
    :param x_axis_name: The title to be used for x-axis in the S-curves plot.
    :param x_log_scale: Whether to make x dimension log scaled. Default True.
    :param x_major_gridlines_visible: Whether to show major gridlines along x. Default True.
    :param x_minor_gridlines_visible: Whether to show minor gridlines along x. Default True.
    :param x_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param x_axis_major_gridline_color: Color to use for gridlines. Default is "#F2F2F2".
    :param y_axis_name: The title to be used for the y-axis in the S-curves plot.
    :param y_min: The minimum percentage value to show.
    :param y_max: The maximum percentage value to show.
    :param y_major_gridlines_visible: Whether to show major gridlines along y. Default True.
    :param y_minor_gridlines_visible: Whether to show minor gridlines along y. Default False.
    :param y_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param y_axis_major_gridline_color: Color to use for gridlines. Default is "#BFBFBF".
    :param show_legend: Whether to show legend on the plot. Default False.
    :param excel_style: The style which excel uses for the plots. Default is 10, which is the default style used by excel.
    :param sort_columns: Whether to sort the keys of the dictionary (uses Python sort). Default True.
    """

    # use the key word arguments to construct the settings used for x and y axes
    x_axis_settings, y_axis_settings = make_chart_settings(locals())

    if sort_keys:
        total_dict = {k: v for k, v in sorted(total_dict.items())}

    with pd.ExcelWriter(output_name) as writer:
        
        workbook = writer.book

        # iterate over all properties, such as iqa, q00, etc.
        for sheet_name in total_dict.keys():

            start_row = 2
            start_col = 7
            atom_names = natsorted(total_dict[sheet_name].keys(), key=ignore_alpha)

            # make graphs to plot later once data is added
            atomic_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )

            start_col += 4
            # get the atom names from the inner dictionary (see get_true_predicted function above)
            ####################################
            # INDIVIDUAL ATOM OVERLAPPED S-CURVE
            ####################################

            # write out individual atom data to sheet
            for atom_name in atom_names:

                # make data to write to an workbook using pandas
                data = {
                    "True": total_dict[sheet_name][atom_name]["true"],
                    "Predicted": total_dict[sheet_name][atom_name]["predicted"],
                    "Error": total_dict[sheet_name][atom_name]["error"],
                }

                df = pd.DataFrame(data)
                df["Error"] = df["Error"].abs()
                # sort whole df by error column (ascending)
                df.sort_values("Error", inplace=True)
                # add percentage column after sorting by error
                ndata = len(df["Error"])
                df["%"] = percentile(ndata)
                end_row = ndata + 1
                # add the atom name above the df
                # write the df for individual atoms
                df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    startrow=1,
                    startcol=start_col,
                )

                rmse_val = np.sqrt(df["Error"].abs().pow(2).sum()/ndata)
                mae_val = df["Error"].abs().sum()/ndata

                writer.sheets[sheet_name].write(0, start_col, atom_name)
                writer.sheets[sheet_name].write(0, start_col+1, "RMSE")
                writer.sheets[sheet_name].write(0, start_col+2, rmse_val)
                writer.sheets[sheet_name].write(0, start_col+3, "MAE")
                writer.sheets[sheet_name].write(0, start_col+4, mae_val)

                atomic_s_curve.add_series(
                    {
                        "name": atom_name,
                        "categories": [
                            sheet_name,
                            start_row,
                            start_col + 3,
                            end_row,
                            start_col + 3,
                        ],
                        "values": [
                            sheet_name,
                            start_row,
                            start_col + 4,
                            end_row,
                            start_col + 4,
                        ],
                        "line": {"width": 1.5},
                    }
                )

                start_col += 6

            # Configure graph with overlapping S-curves for all atoms
            atomic_s_curve.set_x_axis(x_axis_settings)
            atomic_s_curve.set_y_axis(y_axis_settings)
            if show_legend:
                atomic_s_curve.set_legend({"position": "right"})
            atomic_s_curve.set_style(excel_style)
            atomic_s_curve.set_title({"name": "Individual Atom S-Curve"})
            atomic_s_curve.set_size({"width": 650, "height": 520})

            writer.sheets[sheet_name].insert_chart("A10", atomic_s_curve)

def calculate_compact_s_curves_from_files(
    csv_files_list: List[Union[Path, str]],
    models: Models,
    output_location: Union[str, Path] = "s_curves_from_df.xlsx",
    property_names: List[str] = None,
    **kwargs,
):
    """Calculates S-curves used to check model prediction performance. 

    :param csv_files_list: A list of .csv files that contain features columns and property columns.
    :param models: A `Models` instance which contains model files
    :param output_location: The name of the .xlsx file where to save the s-curves.
    :param property_names: A list of strings to use for property column names. If left as None,
        a default set of property names is used
    :param kwargs: Key word argument to give to xlsxwriter for customizing plots.
     """

    nfeatures = models[0].x.shape[-1]
    # dicts to read in csv data
    features_dict: Dict[str, np.ndarray] = {}
    true_values_dict: Dict[str, Dict[str, np.ndarray]] = {}
    # property names
    if not property_names:
        # sum_iqa compared to wfn_energy
        all_props = ["iqa", "wfn_energy"] + multipole_names
    else:
        all_props = property_names

    # use this to get features columns from df
    features_list = [f"f{i}" for i in range(1,nfeatures+1)]

    for csv_file in csv_files_list:

        test_set_df = pd.read_csv(csv_file)

        # make sure that the property iqa / iqa_energy has the correct name
        # if "iqa" found, then replace in all_props
        df_cols = test_set_df.columns

        # add wfn energy to always have access to it in case doing sum of iqa
        if "wfn_energy" in df_cols:
            all_props.append("wfn_energy")

        if "iqa" in df_cols:
            for pr_idx, pr in enumerate(all_props):
                if pr == "iqa_energy":
                    all_props[pr_idx] = "iqa"

        atom_name = csv_file.name.split("_")[0]

        true_values_dict[atom_name] = {}

        for prop in all_props:

            features_dict[atom_name] = test_set_df[features_list].values
            true_values_dict[atom_name][prop] = test_set_df[prop].values

    # get a nested dict of dict of dict of .... https://stackoverflow.com/a/8702435
    nested_dict = lambda: defaultdict(nested_dict)
    total_dict = nested_dict()

    for model in models:
        atom_name = model.atom_name
        property_name = model.prop
        # get features array for atom
        features_array_for_atom = features_dict.get(atom_name)

        # check to see if the passed data contains the infromation that the model needs
        if (features_array_for_atom is not None) and (true_values_dict.get(atom_name) is not None):

            # in case models have "iqa" written as property, but csv file has "iqa_energy"
            if property_name == "iqa" and "iqa_energy" in true_values_dict[atom_name].keys():
                property_name = "iqa"
            # get true values for property
            atomic_true_values = true_values_dict[atom_name].get(property_name)

            if atomic_true_values is not None:

                model_predictions = model.predict(features_array_for_atom)
                errors = atomic_true_values - model_predictions

                if property_name in ("iqa_energy", "iqa", "wfn_energy"):
                    errors *= 2625.5

                total_dict[property_name][atom_name]["true"] = atomic_true_values
                total_dict[property_name][atom_name]["predicted"] = model_predictions
                total_dict[property_name][atom_name]["error"] = errors
            
            else:
                print(f"Could not get value for atom/property: {atom_name}/{property_name} from model file {model.path}.")
        else:
            print(f"Could not get features or true values for atom {atom_name}. Current property: {property_name}, current model file: {model.path}.")

    # if we have iqa energy we can compare to wfn energy
    if "iqa" in total_dict.keys() and "wfn_energy" in true_values_dict[list(true_values_dict.keys())[0]]:
        # get arrays of predictions for iqa energies, sum and compare to wfn energy
        # shape is n_atoms x n_points
        tmp = [inner_dict["predicted"] for atom_name, inner_dict in total_dict["iqa"].items()]
        total_sums = np.sum(tmp, axis=0)
        total_dict["sum_iqa"]["sum_iqa"]["predicted"] =  total_sums
        # assumes the test set is made from the same geometries for all atoms!!!, so then the wfn energy is the same between all datasets
        total_dict["sum_iqa"]["sum_iqa"]["true"] = true_values_dict[list(true_values_dict.keys())[0]].get("wfn_energy")
        errors = true_values_dict[list(true_values_dict.keys())[0]].get("wfn_energy") - total_sums
        total_dict["sum_iqa_vs_wfn"]["sum_iqa"]["error"] =  errors * 2625.5

        errors_sum = []
        # sum up the absolute errors of each atom
        for atom_name in total_dict["iqa"].keys():
            errors_sum.append(total_dict["iqa"][atom_name]["error"])
        errors_sum = np.sum(np.abs(np.array(errors_sum)), axis=0)

        total_dict["sum_iqa_error"]["sum_iqa_error"]["error"] =  errors_sum
        total_dict["sum_iqa_error"]["sum_iqa_error"]["predicted"] = errors_sum
        total_dict["sum_iqa_error"]["sum_iqa_error"]["true"] = np.zeros_like(errors_sum)

    simplified_write_to_excel(total_dict, output_location, **kwargs)

# TODO: remove code duplication
def calculate_compact_s_curves_from_true_predicted(
    predicted_values_dict: Dict[str, Dict[str, np.ndarray]],
    true_values_dict: Dict[str, Dict[str, np.ndarray]],
    output_location: Union[str, Path] = "s_curves_from_df.xlsx",
    **kwargs
):
    """Make s-curves from dictionary of predicted values and dictionary of true values

    :param predicted_values_dict:  A dict of key: atom_name val inner_dict.
        inner_dict of key: property_name, values: 1D np.ndarray containing predicted data for all points 
    :param true_values_dict: A dict of key: atom_name val inner_dict.
        inner_dict of key: property_name, values: 1D np.ndarray containing true data for all points 
    :param output_location: The name of the output .xlsx file, defaults to "s_curves_from_df.xlsx"
    """

   # get a nested dict of dict of dict of .... https://stackoverflow.com/a/8702435
    nested_dict = lambda: defaultdict(nested_dict)
    total_dict = nested_dict()

    atom_names = list(predicted_values_dict.keys())
    property_names = list(predicted_values_dict[atom_names[0]].keys())

    for atom_name in atom_names:

        for property_name in property_names:

            # get true values for property
            atomic_true_values = true_values_dict[atom_name][property_name]
            predicted = predicted_values_dict[atom_name][property_name]

            errors = atomic_true_values - predicted

            if property_name in ("iqa_energy", "iqa", "wfn_energy"):
                errors *= 2625.5

            total_dict[property_name][atom_name]["true"] = atomic_true_values
            total_dict[property_name][atom_name]["predicted"] = predicted
            total_dict[property_name][atom_name]["error"] = errors

    simplified_write_to_excel(total_dict, output_location, sort_keys=False, **kwargs)


######################
# LEGACY FUNCTIONS, SHOULD NOT REALLY BE USED, MIGHT DELETE IN FUTURE
##########################

def calculate_compact_s_curves(
    model_location: Path,
    validation_set_location: Path,
    output_location: Path,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    **kwargs,
):
    """Calculates S-curves used to check model prediction performance. Writes the S-curves to an excel file.

    :param model_location: A directory containing model files `.model`
    :param validation_set_location: A directory containing validation or test set points. These points should NOT be in the training set.
    :param atoms: A list of atom names, eg. O1, H2, C3, etc. for which to make S-curves. S-curves are made for all atoms in the system by default.
    :param types: A list of property types, such as iqa, q00, etc. for which to make S-curves. S-curves are made for all properties in the model files.
    :param **kwargs: Any key word arguments that can be passed into the write_to_excel function to change how the S-curves excel file looks. See write_to_excel() method
    """

    if model_location is None or validation_set_location is None:
        raise ValueError(
            "Enter valid locations for models and validation sets."
        )

    model = Models(model_location)
    validation_set = PointsDirectory(validation_set_location)
    true, predicted = get_true_predicted(model, validation_set, atoms, types)

    write_to_excel(true, predicted, output_location, **kwargs)

def write_to_excel(
    true: pd.DataFrame,
    predicted: pd.DataFrame,
    output_name: Path = "s-curves.xlsx",
    x_axis_name: str = "Absolute Prediction Error",
    x_log_scale: bool = True,
    x_major_gridlines_visible: bool = True,
    x_minor_gridlines_visible: bool = True,
    x_axis_major_gridline_width: int = 0.75,
    x_axis_major_gridline_color: str = "#F2F2F2",
    y_axis_name: str = "%",
    y_min: int = 0,
    y_max: int = 100,
    y_major_gridlines_visible: bool = True,
    y_minor_gridlines_visible: bool = False,
    y_axis_major_gridline_width: int = 0.75,
    y_axis_major_gridline_color: str = "#BFBFBF",
    show_legend: bool = False,
    excel_style: int = 10,
):
    """
    Writes out relevant information which is used to make s-curves to an excel file. It will make a separate sheet for every atom (and property). It
    also makes a `Total` sheet for every property, which gives an idea how the predictions do overall for the whole system.

    :param true: a ModelsResult containing true values (as caluclated by AIMALL) for the validation/test set
    :param predicted: a ModelsResult containing predicted values, given the validation/test set features
    :param output_name: The name of the excel file to be written out.
    :param x_axis_name: The title to be used for x-axis in the S-curves plot.
    :param x_log_scale: Whether to make x dimension log scaled. Default True.
    :param x_major_gridlines_visible: Whether to show major gridlines along x. Default True.
    :param x_minor_gridlines_visible: Whether to show minor gridlines along x. Default True.
    :param x_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param x_axis_major_gridline_color: Color to use for gridlines. Default is "#F2F2F2".
    :param y_axis_name: The title to be used for the y-axis in the S-curves plot.
    :param y_min: The minimum percentage value to show.
    :param y_max: The maximum percentage value to show.
    :param y_major_gridlines_visible: Whether to show major gridlines along y. Default True.
    :param y_minor_gridlines_visible: Whether to show minor gridlines along y. Default False.
    :param y_axis_major_gridline_width: The width to use for the major gridlines. Default is 0.75.
    :param y_axis_major_gridline_color: Color to use for gridlines. Default is "#BFBFBF".
    :param show_legend: Whether to show legend on the plot. Default False.
    :param excel_style: The style which excel uses for the plots. Default is 10, which is the default style used by excel.
    """

    # use the key word arguments to construct the settings used for x and y axes
    x_axis_settings, y_axis_settings = make_chart_settings(locals())

    # transpose to get keys to be the properties (iqa, q00, etc.) instead of them being the values
    true = true.T
    predicted = predicted.T
    # error is still a ModelResult
    error = true - predicted  # .abs()
    # sort to get properties to be ordered nicely
    true = {k: v for k, v in sorted(true.items())}

    with pd.ExcelWriter(output_name) as writer:
        workbook = writer.book

        # iterate over all properties, such as iqa, q00, etc.
        for sheet_name in true.keys():

            start_row = 2
            start_col = 12

            # iqa predictions are in Hartrees, convert to kJ mol-1
            if sheet_name == "iqa":
                error[sheet_name] *= ha_to_kj_mol

            # make graphs to plot later once data is added
            atomic_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )
            total_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )

            ############################
            # TOTAL S-CURVE
            ############################

            # calculate a total df that sums up all the errors for all atoms in one point and then sorts by error (ascending)
            # see ModelResult reduce method
            df = pd.DataFrame(error[sheet_name].reduce())
            df.rename(columns={0: "Total"}, inplace=True)
            df["Total"] = df["Total"].abs()
            df.sort_values("Total", inplace=True)
            ndata = len(df["Total"])
            df["%"] = percentile(ndata)
            # the end row is one more because the df starts one row down
            end_row = ndata + 1
            df.to_excel(
                writer, sheet_name=sheet_name, startrow=1, startcol=start_col
            )
            writer.sheets[sheet_name].write(0, start_col, "Total")

            total_s_curve.add_series(
                {
                    "categories": [
                        sheet_name,
                        start_row,
                        start_col + 1,
                        end_row,
                        start_col + 1,
                    ],
                    "values": [
                        sheet_name,
                        start_row,
                        start_col + 2,
                        end_row,
                        start_col + 2,
                    ],
                    "line": {"width": 1.5},
                }
            )

            # Configure total prediction error S-curve
            total_s_curve.set_x_axis(x_axis_settings)
            total_s_curve.set_y_axis(y_axis_settings)
            total_s_curve.set_legend({"position": "none"})
            total_s_curve.set_style(excel_style)
            total_s_curve.set_title({"name": "Total S-Curve"})
            total_s_curve.set_size({"width": 650, "height": 520})

            writer.sheets[sheet_name].insert_chart("A1", total_s_curve)

            start_col += 4

            # get the atom names from the inner dictionary (see get_true_predicted function above)
            atom_names = natsorted(true[sheet_name].keys(), key=ignore_alpha)
            ####################################
            # INDIVIDUAL ATOM OVERLAPPED S-CURVE
            ####################################

            # write out individual atom data to sheet
            for atom_name in atom_names:

                # make data to write to an workbook using pandas
                data = {
                    "True": true[sheet_name][atom_name],
                    "Predicted": predicted[sheet_name][atom_name],
                    "Error": error[sheet_name][atom_name],
                }
                df = pd.DataFrame(data)
                df["Error"] = df["Error"].abs()
                # sort whole df by error column (ascending)
                df.sort_values("Error", inplace=True)
                # add percentage column after sorting by error
                ndata = len(df["Error"])
                df["%"] = percentile(ndata)
                end_row = ndata + 1
                # add the atom name above the df
                # write the df for individual atoms
                df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    startrow=1,
                    startcol=start_col,
                )
                writer.sheets[sheet_name].write(0, start_col, atom_name)

                atomic_s_curve.add_series(
                    {
                        "name": atom_name,
                        "categories": [
                            sheet_name,
                            start_row,
                            start_col + 3,
                            end_row,
                            start_col + 3,
                        ],
                        "values": [
                            sheet_name,
                            start_row,
                            start_col + 4,
                            end_row,
                            start_col + 4,
                        ],
                        "line": {"width": 1.5},
                    }
                )

                start_col += 6

            # Configure graph with overlapping S-curves for all atoms
            atomic_s_curve.set_x_axis(x_axis_settings)
            atomic_s_curve.set_y_axis(y_axis_settings)
            if show_legend:
                atomic_s_curve.set_legend({"position": "right"})
            atomic_s_curve.set_style(excel_style)
            atomic_s_curve.set_title({"name": "Individual Atom S-Curve"})
            atomic_s_curve.set_size({"width": 650, "height": 520})

            writer.sheets[sheet_name].insert_chart("A27", atomic_s_curve)
