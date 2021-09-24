from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from ichor.analysis.excel import num2col
from ichor.analysis.predictions import get_true_predicted
from ichor.models import Models, ModelsResult
from ichor.points import PointsDirectory
from ichor.constants import ha_to_kj_mol

def percentile(n: int) -> np.ndarray:
    return np.linspace(100 / n, 100, n)


def make_chart_settings(local_kwargs):

    from collections import defaultdict

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
    y_axis_settings["y_axis_name"] = local_kwargs["y_axis_name"]
    y_axis_settings["min"] = local_kwargs["y_min"]
    y_axis_settings["max"] = local_kwargs["y_max"]
    y_axis_settings["major_gridlines"]["visible"] = local_kwargs["y_major_gridlines_visible"]
    y_axis_settings["minor_gridlines"]["visible"] = local_kwargs["y_minor_gridlines_visible"]
    x_axis_settings["major_gridlines"]["line"] = {"width": local_kwargs["y_axis_major_gridline_width"], "color": local_kwargs["y_axis_major_gridline_color"]}

    return x_axis_settings, y_axis_settings

def calculate_s_curves(
    model_location: Path,
    validation_set_location: Path,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    **kwargs,
):
    """ Calculates S-curves used to check model prediction performance. Writes the S-curves to an excel file.
    
    :param model_location: A directory containing model files `.model`
    :param validation_set_location: A directory containing validation or test set points. These points should NOT be in the training set.
    :param atoms: A list of atom names, eg. O1, H2, C3, etc. for which to make S-curves. S-curves are made for all atoms in the system by default.
    :param types: A list of property types, such as iqa, q00, etc. for which to make S-curves. S-curves are made for all properties in the model files.
    :param **kwargs: Any key word arguments that can be passed into the write_to_excel function to change how the S-curves excel file looks. See write_to_excel() method
    """

    if model_location is None or validation_set_location is None:
        raise ValueError("Enter valid locations for models and validation sets.")

    model = Models(model_location)
    validation_set = PointsDirectory(validation_set_location)
    true, predicted = get_true_predicted(model, validation_set, atoms, types)

    write_to_excel(true, predicted, **kwargs)


def write_to_excel(
    true: ModelsResult,
    predicted: ModelsResult,
    output_name: Path = "s-curves.xlsx",
    x_axis_name:str = "Absolute Prediction Error",
    x_log_scale:bool = True,
    x_major_gridlines_visible:bool = True,
    x_minor_gridlines_visible:bool = True,
    x_axis_major_gridline_width = 0.75,
    x_axis_major_gridline_color = "#F2F2F2",
    y_axis_name:str = "%",
    y_min:int = 0,
    y_max:int = 100,
    y_major_gridlines_visible:bool = True,
    y_minor_gridlines_visible:bool = False,
    y_axis_major_gridline_width = 0.75,
    y_axis_major_gridline_color = "#BFBFBF",
    show_legend:bool = False,
    excel_style:int = 10
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
    :param y_axis_name: The title to be used for the y-axis in the S-curves plot.
    :param y_min: The minimum percentage value to show.
    :param y_max: The maximum percentage value to show.
    :param y_major_gridlines_visible: Whether to show major gridlines along y. Default True.
    :param y_minor_gridlines_visible: Whether to show minor gridlines along y. Default False.
    :param show_legend: Whether to show legend on the plot. Default False.
    :param excel_style: The style which excel uses for the plots. Default is 10, which is the default style used by excel.
    """

    # use the key word arguments to construct the settings used for x and y axes
    x_axis_settings, y_axis_settings = make_chart_settings(locals())

    true = true.T
    predicted = predicted.T
    # error is still a ModelResult
    error = (true - predicted).abs()

    with pd.ExcelWriter(output_name) as writer:
        workbook = writer.book

        # iterate over all properties, such as iqa, q00, etc.
        for type_ in true.keys():

            # iqa predictions are in Hartrees, convert to kJ mol-1
            if type_ == "iqa":
                error[type_] *= ha_to_kj_mol
            atom_sheets = {}

            # our true values dictionary only contains info about atoms that we care about (see get_true_predicted function above)
            atom_names = true[type_].keys()
            # iterate over all atoms that have this property calculated
            for atom in atom_names:

                sheet_name = f"{atom}_{type_}"
                atom_sheets[atom] = sheet_name

                # make data to write to an workbook using pandas
                data = {
                    "True": true[type_][atom],
                    "Predicted": predicted[type_][atom],
                    "Error": error[type_][atom],
                }
                df = pd.DataFrame(data)
                df.sort_values("Error", inplace=True)
                # add percentage column after sorting by error
                df["%"] = percentile(len(df["Error"]))
                df.to_excel(writer, sheet_name=sheet_name)

                # add the s-curve to the written sheet
                s_curve = workbook.add_chart(
                    {"type": "scatter", "subtype": "straight"}
                )

                # we always have the error in the 3rd column. The rows start at 1 and end in len(df)
                s_curve.add_series(
                    {
                        # starting row idx, starting col idx, ending row idx, ending col idx
                        "categories": [sheet_name, 1, 3, len(df["Error"]), 3],
                        "values": [sheet_name, 1, 4, len(df["%"]), 4],
                        "line": {"width": 1.5},
                    }
                )

                # Configure S-curves for individual atoms
                s_curve.set_x_axis(x_axis_settings)
                s_curve.set_y_axis(y_axis_settings)
                s_curve.set_legend({"position": "none"})
                s_curve.set_style(excel_style) # default style of excel plots
                writer.sheets[sheet_name].insert_chart("G2", s_curve)

            # also make a sheet with total errors for the whole system (for every property)
            df = pd.DataFrame(error[type_])
            df["Total"] = error[type_].reduce()
            df.sort_values("Total", inplace=True)
            ndata = len(df["Total"])
            df["%"] = percentile(ndata)
            sheet_name = f"Total_{type_}"
            # write df to excel file
            df.to_excel(writer, sheet_name=sheet_name)

            total_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )
            total_s_curve.add_series(
                {
                    "categories": [
                        sheet_name,
                        1,
                        len(atom_names) + 1,
                        ndata,
                        len(atom_names) + 1,
                    ],
                    "values": [
                        sheet_name,
                        1,
                        len(atom_names) + 2,
                        ndata,
                        len(atom_names) + 2,
                    ],
                    "line": {"width": 1.5},
                }
            )

            # Configure total prediction error S-curve
            total_s_curve.set_x_axis(x_axis_settings)
            total_s_curve.set_y_axis(y_axis_settings)
            total_s_curve.set_legend({"position": "none"})
            total_s_curve.set_style(excel_style)


            # below the total s_curve, make an S-curve which overlaps all the individual atom S-curves
            atomic_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )

            for atom_name in atom_names:
                atomic_s_curve.add_series(
                    {
                        "name": atom_name,
                        "categories": [atom_sheets[atom_name], 1, 3, ndata, 3],
                        "values": [atom_sheets[atom_name], 1, 4, ndata, 4],
                        "line": {"width": 1.5},
                    }
                )

            # Configure graph with overlapping S-curves for all atoms
            atomic_s_curve.set_x_axis(x_axis_settings)
            atomic_s_curve.set_y_axis(y_axis_settings)
            if show_legend:
                atomic_s_curve.set_legend({"position": "right"})
            atomic_s_curve.set_style(excel_style)

            writer.sheets[sheet_name].insert_chart(
                f"{num2col(len(atom_names)+5)}2", total_s_curve
            )
            writer.sheets[sheet_name].insert_chart(
                f"{num2col(len(atom_names)+5)}18", atomic_s_curve
            )