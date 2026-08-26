import colorsys
import re
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from ichor.core.analysis.predictions import get_true_predicted
from ichor.core.common.constants import ha_to_kj_mol, multipole_names
from ichor.core.common.sorting import ignore_alpha
from ichor.core.files import PointsDirectory
from ichor.core.models import Models
from natsort import natsorted
from tqdm import tqdm

# FEREBUS/ichor training CSVs are named "<system>_<atom>_<SETTYPE>_SET.csv" where
# the system name itself may contain underscores, so the atom name is recovered by
# stripping the known set-type suffix and taking the final token.
FEREBUS_SET_SUFFIXES = (
    "_EXT_VALIDATION_SET",
    "_INT_VALIDATION_SET",
    "_TRAINING_SET",
)

# feature columns in FEREBUS training CSVs are named f1, f2, ... fN
FEATURE_COLUMN_RE = re.compile(r"^f\d+$")


def atom_name_from_ferebus_csv(filename: Union[str, Path]) -> str:
    """Extracts the atom name (e.g. ``C5``) from a FEREBUS/ichor training CSV file
    name such as ``BZAMID05_MOL_MTD_OUT0_C5_EXT_VALIDATION_SET.csv``.

    :param filename: The CSV file name (or path).
    :return: The atom name, taken as the token before the set-type suffix.
    """

    stem = Path(filename).stem  # drops the .csv extension
    for suffix in FEREBUS_SET_SUFFIXES:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.rsplit("_", 1)[-1]


def ferebus_csv_index(
    csv_files_list: List[Union[str, Path]]
) -> Dict[Tuple[str, str], Tuple[np.ndarray, np.ndarray]]:
    """Reads FEREBUS/ichor per-(atom, property) training-style CSVs and indexes their
    contents by ``(atom name, property name)`` so they can be matched to models.

    Each CSV is expected to contain feature columns named ``f1, f2, ...`` and a
    single property column named after the property (e.g. ``q43s``, ``iqa``). The
    atom name is taken from the file name (see :func:`atom_name_from_ferebus_csv`).

    :param csv_files_list: A list of per-(atom, property) CSV files. These should
        all be of a single split (e.g. only the EXT_VALIDATION_SET files).
    :return: a dict mapping ``(atom, property)`` to a tuple of the 2D feature array
        and the 1D array of true values.
    """

    csv_index: Dict[Tuple[str, str], Tuple[np.ndarray, np.ndarray]] = {}
    for csv_file in tqdm(csv_files_list, desc="Reading CSVs"):
        csv_file = Path(csv_file)
        df = pd.read_csv(csv_file)

        feature_cols = [c for c in df.columns if FEATURE_COLUMN_RE.match(str(c))]
        property_cols = [c for c in df.columns if c not in feature_cols]

        if not feature_cols or not property_cols:
            print(
                f"Skipping {csv_file.name}: could not identify feature/property columns."
            )
            continue

        # the property column is the (single) non-feature column, named after the property
        property_name = str(property_cols[-1])
        atom_name = atom_name_from_ferebus_csv(csv_file.name)
        csv_index[(atom_name, property_name)] = (
            df[feature_cols].values,
            df[property_name].values,
        )

    return csv_index


def match_model_to_csv_key(
    csv_index: Dict[Tuple[str, str], tuple], atom_name: str, property_name: str
) -> Optional[Tuple[str, str]]:
    """Finds the key of ``csv_index`` holding the data for a model of ``property_name``
    on ``atom_name``, allowing for the iqa/iqa_energy naming difference (models can
    call the property ``iqa`` where the CSV column is ``iqa_energy``, or vice versa).

    :param csv_index: an index as returned by :func:`ferebus_csv_index`.
    :param atom_name: the model's atom name, e.g. ``C5``.
    :param property_name: the model's property name, e.g. ``iqa``.
    :return: the matching key, or ``None`` if the index holds no data for the model.
    """

    key = (atom_name, property_name)
    if key in csv_index:
        return key

    for alias, other in (("iqa", "iqa_energy"), ("iqa_energy", "iqa")):
        if property_name == alias and (atom_name, other) in csv_index:
            return (atom_name, other)

    return None


def true_predicted_from_ferebus_csvs(
    csv_files_list: List[Union[str, Path]],
    models: Models,
    energy_scale: float = ha_to_kj_mol,
) -> dict:
    """Reads FEREBUS/ichor per-(atom, property) training-style CSVs and uses the
    given models to predict, returning the nested dict used to make S-curves and
    metrics.

    Each CSV is expected to contain feature columns named ``f1, f2, ...`` and a
    single property column named after the property (e.g. ``q43s``, ``iqa``). The
    atom name is taken from the file name (see :func:`atom_name_from_ferebus_csv`).
    Only (atom, property) pairs for which both a CSV and a model exist are included.

    :param csv_files_list: A list of per-(atom, property) CSV files. These should
        all be of a single held-out split (e.g. only the EXT_VALIDATION_SET files).
    :param models: A ``Models`` instance containing the ``.model`` files.
    :param energy_scale: Factor applied to energy errors (iqa/wfn) so they are in
        kJ mol-1. Multipole errors are left in atomic units.
    :return: a nested dict ``{property: {atom: {"true", "predicted", "error"}}}``
        (energy errors already scaled to kJ mol-1).
    """

    # index the CSV data by (atom, property) so it can be matched to each model
    csv_index = ferebus_csv_index(csv_files_list)

    # get a nested dict of dict of dict of .... https://stackoverflow.com/a/8702435
    nested_dict = lambda: defaultdict(nested_dict)  # noqa: E731
    total_dict = nested_dict()

    for model in tqdm(models, desc="Predicting"):
        atom_name = model.atom_name
        property_name = model.prop

        key = match_model_to_csv_key(csv_index, atom_name, property_name)
        if key is None:
            continue

        features_array, true_values = csv_index[key]
        predicted = model.predict(features_array)
        errors = true_values - predicted

        if property_name in ("iqa_energy", "iqa", "wfn_energy"):
            errors = errors * energy_scale

        total_dict[property_name][atom_name]["true"] = true_values
        total_dict[property_name][atom_name]["predicted"] = predicted
        total_dict[property_name][atom_name]["error"] = errors

    return total_dict


def percentile(n: int) -> np.ndarray:
    return np.linspace(100 / n, 100, n)


def make_chart_settings(local_kwargs: dict):
    """Takes in a dictionary of key word arguments that were
    passed into the ``write_to_excel`` function. Then, this function
    constructs dictionaries with parameter values to be passed
    to xlsx writer to configure graph settings.

    :param local_kwargs: A dictionary containing key word arguments
        that are parsed to construct the xlsx-writer graph settings
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
    sort_keys: bool = True,
):
    """
    Writes out relevant information which is used to make s-curves to an excel file.
    It will make a separate sheet for every atom (and property). It
    also makes a ``Total`` sheet for every property,
    which gives an idea how the predictions do overall for the whole system.

    :param total_dict: a dictionary containing key: property, val: inner_dict.
        inner_dict contains key: atom_name, val: inner_inner_dict.
        inner_inner_dict contains key: (true, predicted or error),
        val: a 1D numpy array containing the corresponding values
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
    :param excel_style: The style which excel uses for the plots.
        Default is 10, which is the default style used by excel.
    :param sort_columns: Whether to sort the keys of the dictionary (uses Python sort). Default True.
    """

    # use the key word arguments to construct the settings used for x and y axes
    x_axis_settings, y_axis_settings = make_chart_settings(locals())

    if sort_keys:
        total_dict = {k: v for k, v in sorted(total_dict.items())}

    with pd.ExcelWriter(output_name) as writer:

        workbook = writer.book

        # iterate over all properties, such as iqa, q00, etc.
        for sheet_name in tqdm(
            total_dict.keys(),
            desc="Writing S-curve sheets",
            total=len(total_dict),
        ):

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

                rmse_val = np.sqrt(df["Error"].abs().pow(2).sum() / ndata)
                mae_val = df["Error"].abs().sum() / ndata

                writer.sheets[sheet_name].write(0, start_col, atom_name)
                writer.sheets[sheet_name].write(0, start_col + 1, "RMSE")
                writer.sheets[sheet_name].write(0, start_col + 2, rmse_val)
                writer.sheets[sheet_name].write(0, start_col + 3, "MAE")
                writer.sheets[sheet_name].write(0, start_col + 4, mae_val)

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


def true_predicted_dict_from_csv_files(
    csv_files_list: List[Union[Path, str]],
    models: Models,
    property_names: List[str] = None,
) -> Tuple[dict, Dict[str, Dict[str, np.ndarray]]]:
    """Reads per-atom CSV files (features + true property values) and uses the
    given models to predict, returning the data needed to make S-curves or to
    compute quality metrics.

    :param csv_files_list: A list of .csv files that contain feature columns and
        property columns (as written out by ichor). The atom name is taken from
        the part of each file name before the first underscore.
    :param models: A ``Models`` instance which contains the model files.
    :param property_names: A list of property column names to read. If left as
        ``None``, a default set (iqa, wfn_energy and the multipole moments) is used.
    :return: a tuple ``(total_dict, true_values_dict)`` where ``total_dict`` is a
        nested dict ``{property: {atom: {"true", "predicted", "error"}}}`` (energy
        errors are already converted to kJ mol-1) and ``true_values_dict`` is
        ``{atom: {property: array}}`` with the raw (unscaled) true values.
    """

    # dicts to read in csv data
    features_dict: Dict[str, np.ndarray] = {}
    true_values_dict: Dict[str, Dict[str, np.ndarray]] = {}
    # property names
    if not property_names:
        # sum_iqa compared to wfn_energy
        all_props = ["iqa", "wfn_energy"] + multipole_names
    else:
        all_props = property_names

    for csv_file in csv_files_list:

        test_set_df = pd.read_csv(csv_file)

        # these are the indices of the columns that surround the feature columns in the csv
        # if the csvs have been written out by ichor
        index_of_prev_column = test_set_df.columns.get_loc("point_name")
        index_of_subsequent_column = test_set_df.columns.get_loc("wfn_energy")

        # get column names that contain features
        features_list = test_set_df.columns[
            (index_of_prev_column + 1) : index_of_subsequent_column  # noqa
        ]

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

            # only read properties that are actually present in the CSV, so that
            # e.g. an "iqa only" data-prep split (no multipole columns) does not
            # raise a KeyError
            if prop not in df_cols:
                continue

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
        if (features_array_for_atom is not None) and (
            true_values_dict.get(atom_name) is not None
        ):

            # in case models have "iqa" written as property, but csv file has "iqa_energy"
            if (
                property_name == "iqa"
                and "iqa_energy" in true_values_dict[atom_name].keys()
            ):
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
                print(
                    f"Could not get value for atom/property: {atom_name}/{property_name} from model file {model.path}."
                )
        else:
            print(
                f"Could not get features or true values for atom {atom_name}. \
                    Current property: {property_name}, current model file: {model.path}."
            )

    return total_dict, true_values_dict


def calculate_compact_s_curves_from_files(
    csv_files_list: List[Union[Path, str]],
    models: Models,
    output_location: Union[str, Path] = "s_curves_from_df.xlsx",
    property_names: List[str] = None,
    **kwargs,
):
    """Calculates S-curves used to check model prediction performance.

    :param csv_files_list: A list of .csv files that contain features columns and property columns.
    :param models: A ``Models`` instance which contains model files
    :param output_location: The name of the .xlsx file where to save the s-curves.
    :param property_names: A list of strings to use for property column names. If left as None,
        a default set of property names is used
    :param kwargs: Key word argument to give to xlsxwriter for customizing plots.
    """

    total_dict, true_values_dict = true_predicted_dict_from_csv_files(
        csv_files_list, models, property_names
    )

    # if we have iqa energy we can compare to wfn energy
    if (
        "iqa" in total_dict.keys()
        and "wfn_energy" in true_values_dict[list(true_values_dict.keys())[0]]
    ):
        # get arrays of predictions for iqa energies, sum and compare to wfn energy
        # shape is n_atoms x n_points
        tmp = [
            inner_dict["predicted"]
            for atom_name, inner_dict in total_dict["iqa"].items()
        ]
        total_sums = np.sum(tmp, axis=0)
        total_dict["sum_iqa_vs_wfn"]["sum_iqa"]["predicted"] = total_sums
        # assumes the test set is made from the same geometries for all atoms!!!
        # , so then the wfn energy is the same between all datasets
        total_dict["sum_iqa_vs_wfn"]["sum_iqa"]["true"] = true_values_dict[
            list(true_values_dict.keys())[0]
        ].get("wfn_energy")
        errors = (
            true_values_dict[list(true_values_dict.keys())[0]].get("wfn_energy")
            - total_sums
        )
        total_dict["sum_iqa_vs_wfn"]["sum_iqa"]["error"] = errors * 2625.5

        # errors_sum = []
        # # sum up the absolute errors of each atom
        # for atom_name in total_dict["iqa"].keys():
        #     errors_sum.append(total_dict["iqa"][atom_name]["error"])
        # errors_sum = np.sum(np.abs(np.array(errors_sum)), axis=0)

        # total_dict["sum_iqa_error"]["sum_iqa_error"]["error"] =  errors_sum
        # total_dict["sum_iqa_error"]["sum_iqa_error"]["predicted"] = errors_sum
        # total_dict["sum_iqa_error"]["sum_iqa_error"]["true"] = np.zeros_like(errors_sum)

    simplified_write_to_excel(total_dict, output_location, **kwargs)


# TODO: remove code duplication
def calculate_compact_s_curves_from_true_predicted(
    predicted_values_dict: Dict[str, Dict[str, np.ndarray]],
    true_values_dict: Dict[str, Dict[str, np.ndarray]],
    output_location: Union[str, Path] = "s_curves_from_df.xlsx",
    **kwargs,
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


def mpl_get_true_vals_dict(
    predicted_values_dict: Dict[str, Dict[str, np.ndarray]],
    true_values_dict: Dict[str, Dict[str, np.ndarray]],
) -> dict:
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

            total_dict[property_name][atom_name]["error"] = errors

    return total_dict


# properties whose errors are in kJ mol-1; everything else (multipoles) is in a.u.
_S_CURVE_ENERGY_PROPERTIES = ("iqa", "iqa_energy", "wfn_energy")
_S_CURVE_DEFAULT_X_LABEL = "Prediction Error / kJ mol$^{-1}$"
_S_CURVE_MULTIPOLE_X_LABEL = "Prediction Error / a.u."

# CPK / Jmol-style element colours so that atoms of the same element share a base
# colour across the S-curve plots (oxygen red, nitrogen blue, carbon black, etc.).
# A few colours are darkened relative to the classic CPK values so they stay
# visible against a white plot background. Hydrogen departs from CPK entirely: as
# white/grey it was hard to tell from carbon black, so it is given a hue of its own.
ELEMENT_COLORS = {
    "H": "#12B0C0",  # white in CPK -> teal, so H is not confused with carbon black
    "C": "#000000",  # black
    "N": "#3050F8",  # blue
    "O": "#FF0D0D",  # red
    "F": "#1FA33F",  # green
    "Cl": "#1FC21F",  # green
    "Br": "#A62929",  # dark red / brown
    "I": "#940094",  # purple
    "P": "#FF8000",  # orange
    "S": "#C9A600",  # yellow -> darkened gold for visibility
    "B": "#CC7A7A",  # salmon
    "Si": "#9E7A50",  # tan
    "Na": "#AB5CF2",  # violet
    "Mg": "#4CB000",  # green
    "K": "#8F40D4",  # violet
    "Ca": "#3DBF00",  # green
    "Fe": "#E06633",  # orange-brown
    "Zn": "#7D80B0",  # slate
}

# used for any element not present in ELEMENT_COLORS above
_FALLBACK_ELEMENT_COLORS = [
    "#845B97",
    "#30D5C8",
    "#FA8072",
    "#00B945",
    "#FF9500",
]


def _element_from_atom_name(atom_name: str) -> str:
    """Returns the element symbol from an atom name, e.g. ``O1`` -> ``O``,
    ``CL2`` -> ``Cl``. The leading alphabetic characters are taken as the element
    and normalised to title case so it matches the keys in ``ELEMENT_COLORS``.

    :param atom_name: An atom name such as ``O1``, ``H12`` or ``Cl3``.
    :return: The element symbol (or the original string if no letters are found).
    """

    match = re.match(r"[A-Za-z]+", str(atom_name))
    if not match:
        return str(atom_name)
    token = match.group(0)
    return token[0].upper() + token[1:].lower()


def _element_shades(base_hex: str, n: int) -> List[str]:
    """Returns ``n`` shades of ``base_hex`` that share the same hue but differ in
    lightness, so several atoms of the same element are distinguishable while still
    reading as the same colour. A single atom keeps the exact base colour.

    :param base_hex: The base element colour as a hex string.
    :param n: How many shades (atoms of this element) are needed.
    :return: A list of ``n`` hex colour strings, brightest first.
    """

    import matplotlib.colors as mcolors

    if n <= 1:
        return [base_hex]

    h, lightness, s = colorsys.rgb_to_hls(*mcolors.to_rgb(base_hex))
    # spread lightness in a band centred on the base colour's lightness, so dark
    # bases stay dark and light bases stay light and the two do not collapse onto
    # the same shades. The band is shifted (not just clamped) to keep its full
    # width inside a range visible on a white background. Achromatic elements
    # (carbon black) use a narrower band so their greyscale shades stay in a
    # single dark range; coloured elements use a wider band so their shades are
    # easy to tell apart (hue keeps them distinct from the greys regardless).
    span = 0.26 if s < 0.12 else 0.40
    floor, ceil = 0.15, 0.85
    lo, hi = lightness - span / 2, lightness + span / 2
    if lo < floor:
        hi += floor - lo
        lo = floor
    if hi > ceil:
        lo -= hi - ceil
        hi = ceil
    lo, hi = max(floor, lo), min(ceil, hi)
    lightnesses = np.linspace(hi, lo, n)
    return [mcolors.to_hex(colorsys.hls_to_rgb(h, li, s)) for li in lightnesses]


def element_color_map(atom_names: List[str]) -> Dict[str, str]:
    """Maps each atom name to a colour so that atoms of the same element share a
    base colour (see ``ELEMENT_COLORS``); when an element occurs more than once the
    atoms get different shades of that base colour.

    :param atom_names: The atom names to colour, e.g. ``["O1", "H2", "H3", "C4"]``.
    :return: A dict mapping each atom name to a hex colour string.
    """

    # group atoms by element, preserving the incoming order within each element
    groups: "OrderedDict[str, List[str]]" = OrderedDict()
    for atom_name in atom_names:
        groups.setdefault(_element_from_atom_name(atom_name), []).append(atom_name)

    colors: Dict[str, str] = {}
    fallback_idx = 0
    for element, members in groups.items():
        base = ELEMENT_COLORS.get(element)
        if base is None:
            base = _FALLBACK_ELEMENT_COLORS[
                fallback_idx % len(_FALLBACK_ELEMENT_COLORS)
            ]
            fallback_idx += 1
        for atom_name, color in zip(members, _element_shades(base, len(members))):
            colors[atom_name] = color

    return colors


def group_total_dict_by_element(
    total_dict: Dict[str, Dict[str, object]],
) -> "OrderedDict[str, Dict[str, Dict[str, object]]]":
    """Splits a nested ``{property: {atom: data}}`` dict into one such dict per
    element, i.e. ``{element: {property: {atom: data}}}``. The ``data`` values are
    left untouched (not copied), so this works for both the full
    ``{"true", "predicted", "error"}`` dicts and error-only dicts.

    :param total_dict: nested dict keyed by property then atom.
    :return: an ``OrderedDict`` keyed by element symbol (natsorted), each value a
        ``{property: {atom: data}}`` dict holding only that element's atoms.
    """

    from ichor.core.common.str import get_characters

    grouped: Dict[str, Dict[str, Dict[str, object]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for property_name, atom_dict in total_dict.items():
        for atom_name, data in atom_dict.items():
            element = get_characters(atom_name)
            grouped[element][property_name][atom_name] = data

    # return plain dicts (not defaultdicts) in a stable, natsorted element order
    return OrderedDict(
        (element, {p: dict(a) for p, a in grouped[element].items()})
        for element in natsorted(grouped.keys())
    )


def plot_with_matplotlib(
    total_dict: Union[List[dict], dict],
    x_axis_name: str = _S_CURVE_DEFAULT_X_LABEL,
    y_axis_name: str = "%",
    title: str = None,
    saved_name: str = "s_curves.png",
    panel_width: float = 7.0,
    panel_height: float = 6.0,
    dpi: int = 200,
) -> List[Path]:
    """Plots S-curves, saving a **separate image file for each property**. Every
    property gets its own figure (all atoms overlaid), named after ``saved_name``
    with the property appended, e.g. ``s_curves.png`` -> ``s_curves_iqa.png``,
    ``s_curves_q00.png``, etc.

    :param total_dict: a nested dict ``{property: {atom: {"error": array}}}`` (or a
        list of such dicts, which are merged). Only the ``"error"`` values are
        plotted; if an atom maps directly to an array, that array is used.
    :param x_axis_name: x-axis label (errors are shown on a log scale). If left at
        the default, the units are chosen per property (kJ mol-1 for energies,
        atomic units for multipoles); pass a custom string to override.
    :param y_axis_name: y-axis label (percentage of points).
    :param title: optional prefix added to each plot's title (the property name is
        always shown).
    :param saved_name: base output file name. The property name is inserted before
        the extension for each file; ``.png`` is recommended for a readable image.
    :param panel_width: width in inches of each per-property figure.
    :param panel_height: height in inches of each per-property figure.
    :param dpi: resolution of the saved figures.
    :return: the list of file paths that were written (empty if nothing was plotted
        or matplotlib is unavailable).
    """

    try:
        import matplotlib

        import matplotlib.pyplot as plt
        from matplotlib import ticker as mticker

        matplotlib.rcParams.update(
            {
                "text.usetex": False,
                "font.family": "sans-serif",
                "font.serif": "DejaVu Serif",
                "axes.formatter.use_mathtext": False,
                "mathtext.fontset": "dejavusans",
            }
        )

    except ImportError:
        print("Could not import relevant packages.")

        return []

    TITLE_FONTSIZE = 18
    X_Y_LABELS_FONTSIZE = 16
    TICKLABELS_FONTSIZE = 12
    LEGEND_FONTSIZE = 10
    LABELPAD = 8
    AXES_PADDING = 6.0
    LINEWIDTH = 2.0
    MINOR_LINEWIDTH = 1.3
    MAJOR_TICK_LENGTH = 5.0
    MINOR_TICK_LENGTH = 3.0

    # accept a list of dicts (legacy) by merging into one property -> atoms dict
    if isinstance(total_dict, (list, tuple)):
        merged = {}
        for d in total_dict:
            merged.update(d)
        total_dict = merged

    property_names = natsorted(total_dict.keys(), key=ignore_alpha)
    if len(property_names) == 0:
        print("No data to plot.")
        return []

    base_path = Path(saved_name)
    saved_files: List[Path] = []

    # one separate figure/file per property
    for property_name in tqdm(property_names, desc="Plotting S-curves"):

        fig, ax = plt.subplots(figsize=(panel_width, panel_height))

        inner_dict = total_dict[property_name]
        atom_names = natsorted(inner_dict.keys(), key=ignore_alpha)
        # colour atoms by element (same element -> same base colour, different
        # shades when an element appears more than once)
        atom_colors = element_color_map(atom_names)

        for an in atom_names:

            atom_data = inner_dict[an]
            # support {"error": array}, the full {"true", "predicted", "error"} dict,
            # or an atom that maps directly to an array of errors
            if isinstance(atom_data, dict):
                array = atom_data.get("error")
            else:
                array = atom_data
            if array is None:
                continue

            array_sorted = np.sort(np.absolute(array))
            perc = percentile(array_sorted.shape[0])
            ax.semilogx(
                array_sorted,
                perc,
                label=an,
                linewidth=LINEWIDTH,
                color=atom_colors[an],
            )

        plot_title = f"{title} - {property_name}" if title else str(property_name)
        ax.set_title(plot_title, fontsize=TITLE_FONTSIZE, fontweight="bold")

        if atom_names:
            ax.legend(
                facecolor="white",
                framealpha=0.9,
                frameon=True,
                fontsize=LEGEND_FONTSIZE,
                ncol=2 if len(atom_names) > 8 else 1,
            )

        # major/minor grids
        ax.grid(which="major", color="#DDDDDD", linewidth=LINEWIDTH)
        ax.grid(
            which="minor", color="#EEEEEE", linestyle=":", linewidth=MINOR_LINEWIDTH
        )
        ax.minorticks_on()
        ax.grid(True)

        # when the default label is used, show the correct units per property
        # (kJ mol-1 for energies, atomic units for multipoles); a caller-supplied
        # label is respected as-is
        if x_axis_name == _S_CURVE_DEFAULT_X_LABEL:
            x_label = (
                _S_CURVE_DEFAULT_X_LABEL
                if property_name in _S_CURVE_ENERGY_PROPERTIES
                else _S_CURVE_MULTIPOLE_X_LABEL
            )
        else:
            x_label = x_axis_name

        if x_label:
            ax.set_xlabel(
                x_label,
                fontsize=X_Y_LABELS_FONTSIZE,
                labelpad=LABELPAD,
                fontweight="bold",
            )
        if y_axis_name:
            ax.set_ylabel(
                y_axis_name,
                fontsize=X_Y_LABELS_FONTSIZE,
                labelpad=LABELPAD,
                fontweight="bold",
            )

        ax.xaxis.set_major_locator(mticker.LogLocator(numticks=999))
        ax.xaxis.set_minor_locator(mticker.LogLocator(numticks=999, subs="auto"))

        ax.tick_params(
            axis="both",
            which="major",
            labelsize=TICKLABELS_FONTSIZE,
            length=MAJOR_TICK_LENGTH,
            width=LINEWIDTH,
            top=False,
            right=False,
            pad=AXES_PADDING,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            length=MINOR_TICK_LENGTH,
            width=MINOR_LINEWIDTH,
            top=False,
            right=False,
        )

        # insert the property name before the extension, e.g. s_curves_iqa.png
        out_path = base_path.with_name(
            f"{base_path.stem}_{property_name}{base_path.suffix}"
        )
        fig.tight_layout()
        fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(out_path)

    return saved_files


def plot_s_curves_per_element(
    total_dict: Union[List[dict], dict],
    saved_name: str = "s_curves.png",
    **kwargs,
) -> List[Path]:
    """Plots S-curves separately for each element type, so each element gets its
    own file(s) containing only that element's atoms. The element symbol is
    inserted into the file name (and used as the plot title prefix), and each
    property still gets its own file, e.g. ``s_curves.png`` ->
    ``s_curves_C_iqa.png``, ``s_curves_H_iqa.png``, ``s_curves_O_q00.png``, etc.

    :param total_dict: a nested dict ``{property: {atom: {"error": array}}}`` (or a
        list of such dicts, which are merged), as consumed by
        :func:`plot_with_matplotlib`.
    :param saved_name: base output file name; the element symbol and property name
        are inserted before the extension for each file.
    :param kwargs: any other keyword arguments accepted by
        :func:`plot_with_matplotlib` (e.g. ``dpi``, ``panel_width``). A ``title``
        given here is used as a prefix in front of the element symbol.
    :return: the list of file paths that were written.
    """

    # accept a list of dicts (legacy) by merging into one property -> atoms dict
    if isinstance(total_dict, (list, tuple)):
        merged: dict = {}
        for d in total_dict:
            merged.update(d)
        total_dict = merged

    base_path = Path(saved_name)
    # a caller-supplied title becomes a prefix in front of the element symbol
    outer_title = kwargs.pop("title", None)

    saved_files: List[Path] = []
    for element, element_dict in group_total_dict_by_element(total_dict).items():
        element_saved_name = base_path.with_name(
            f"{base_path.stem}_{element}{base_path.suffix}"
        )
        element_title = f"{outer_title} {element}" if outer_title else element
        saved_files.extend(
            plot_with_matplotlib(
                element_dict,
                saved_name=element_saved_name,
                title=element_title,
                **kwargs,
            )
        )

    return saved_files


def _merge_total_dicts(total_dict: Union[List[dict], dict]) -> dict:
    """Accepts a nested ``{property: {atom: data}}`` dict or a list of such dicts
    (legacy), returning a single merged dict."""
    if isinstance(total_dict, (list, tuple)):
        merged: dict = {}
        for d in total_dict:
            merged.update(d)
        return merged
    return total_dict


def write_s_curves_to_csv(
    total_dict: Union[List[dict], dict],
    saved_name: Union[str, Path] = "s-curves.csv",
) -> List[Path]:
    """Writes the S-curve data (sorted absolute prediction error vs cumulative
    percentage of points) to plain CSV files - a separate file per property, named
    like :func:`plot_with_matplotlib` (e.g. ``s-curves.csv`` -> ``s-curves_iqa.csv``,
    ``s-curves_q00.csv``). Each atom contributes two columns, ``<atom>_error`` (the
    sorted absolute error) and ``<atom>_%`` (the cumulative percentage), so the file
    holds exactly the numbers behind the plotted S-curves. Atoms with fewer points
    leave the tail of their columns blank.

    :param total_dict: a nested dict ``{property: {atom: {"error": array}}}`` (or the
        full ``{"true", "predicted", "error"}`` dict, or an atom mapping directly to
        an array of errors), as consumed by :func:`plot_with_matplotlib`; a list of
        such dicts is merged.
    :param saved_name: base output file name; the property name is inserted before
        the ``.csv`` extension for each file.
    :return: the list of file paths that were written (empty if there was no data).
    """

    total_dict = _merge_total_dicts(total_dict)

    base_path = Path(saved_name)
    property_names = natsorted(total_dict.keys(), key=ignore_alpha)
    saved_files: List[Path] = []

    for property_name in tqdm(property_names, desc="Writing S-curve CSVs"):
        inner_dict = total_dict[property_name]
        atom_names = natsorted(inner_dict.keys(), key=ignore_alpha)

        columns: "OrderedDict[str, pd.Series]" = OrderedDict()
        for an in atom_names:
            atom_data = inner_dict[an]
            # support {"error": array}, the full {"true", "predicted", "error"} dict,
            # or an atom that maps directly to an array of errors
            if isinstance(atom_data, dict):
                array = atom_data.get("error")
            else:
                array = atom_data
            if array is None:
                continue

            array_sorted = np.sort(np.absolute(array))
            perc = percentile(array_sorted.shape[0])
            columns[f"{an}_error"] = pd.Series(array_sorted)
            columns[f"{an}_%"] = pd.Series(perc)

        if not columns:
            continue

        # pd.Series columns of differing length align on index, padding the shorter
        # atoms' tails with NaN (written as blank cells)
        df = pd.DataFrame(columns)
        out_path = base_path.with_name(
            f"{base_path.stem}_{property_name}{base_path.suffix}"
        )
        df.to_csv(out_path, index=False)
        saved_files.append(out_path)

    return saved_files


def write_s_curves_to_csv_per_element(
    total_dict: Union[List[dict], dict],
    saved_name: Union[str, Path] = "s-curves.csv",
) -> List[Path]:
    """Like :func:`write_s_curves_to_csv` but writes a separate file per element
    type (each holding only that element's atoms), inserting the element symbol into
    the file name, e.g. ``s-curves_C_iqa.csv``, ``s-curves_H_iqa.csv``.

    :param total_dict: nested dict as consumed by :func:`write_s_curves_to_csv`.
    :param saved_name: base output file name; the element symbol and property name
        are inserted before the extension for each file.
    :return: the list of file paths that were written.
    """

    total_dict = _merge_total_dicts(total_dict)

    base_path = Path(saved_name)
    saved_files: List[Path] = []
    for element, element_dict in group_total_dict_by_element(total_dict).items():
        element_saved_name = base_path.with_name(
            f"{base_path.stem}_{element}{base_path.suffix}"
        )
        saved_files.extend(
            write_s_curves_to_csv(element_dict, saved_name=element_saved_name)
        )
    return saved_files


def write_s_curves_to_excel_per_element(
    total_dict: Union[List[dict], dict],
    saved_name: Union[str, Path] = "s-curves.xlsx",
    **kwargs,
) -> List[Path]:
    """Writes a separate S-curve Excel workbook per element type (each holding only
    that element's atoms), inserting the element symbol into the file name, e.g.
    ``s-curves_C.xlsx``, ``s-curves_H.xlsx``. Each workbook has one sheet per
    property, as produced by :func:`simplified_write_to_excel`.

    :param total_dict: the full nested dict ``{property: {atom: {"true",
        "predicted", "error"}}}`` (the Excel writer needs true/predicted, not just
        errors); a list of such dicts is merged.
    :param saved_name: base output file name; the element symbol is inserted before
        the ``.xlsx`` extension for each file.
    :param kwargs: any other keyword arguments accepted by
        :func:`simplified_write_to_excel`.
    :return: the list of workbook paths that were written.
    """

    total_dict = _merge_total_dicts(total_dict)

    base_path = Path(saved_name)
    saved_files: List[Path] = []
    for element, element_dict in group_total_dict_by_element(total_dict).items():
        element_saved_name = base_path.with_name(
            f"{base_path.stem}_{element}{base_path.suffix}"
        )
        simplified_write_to_excel(element_dict, element_saved_name, **kwargs)
        saved_files.append(element_saved_name)
    return saved_files


def plot_with_matplotlib_simple(
    total_dict: dict,
    x_axis_name: str = "Prediction Error / kJ mol$^{-1}$",
    y_axis_name: str = r"%",
    title: str = None,
):

    try:
        import matplotlib.pyplot as plt

        # import scienceplots  # noqa
    except ImportError:
        print("Could not import relevant packages.")

        return

    # plt.style.use("science")

    fig, ax = plt.subplots(figsize=(9, 9))

    ax.set_prop_cycle(
        color=[
            "0C5DA5",
            "00B945",
            "FF9500",
            "FF2C00",
            "845B97",
            "474747",
            "9e9e9e",
            "30D5C8",
            "FA8072",
        ]
    )

    # property name, inner dict
    for key, inner_dict in total_dict.items():

        # sort atom names so they appear correctly in label
        atom_names = natsorted(inner_dict.keys(), key=ignore_alpha)

        for an in atom_names:

            # true pred err keys , arrays values
            for true_pred_err, array in inner_dict[an].items():

                # true,pred,err keys , array of values
                # should only plot errors for s-curves

                array_sorted = np.sort(np.absolute(array))
                perc = percentile(array_sorted.shape[0])

                ax.plot(array_sorted, perc, label=an, linewidth=2)
                ax.set_xscale("log")

    plt.legend(facecolor="white", framealpha=1, frameon=True, fontsize=24)

    # Show the major grid and style it slightly.
    ax.grid(which="major", color="#DDDDDD", linewidth=2)
    # Show the minor grid as well. Style it in very light gray as a thin,
    # dotted line.
    ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=1.7)
    # Make the minor ticks and gridlines show.
    ax.minorticks_on()
    ax.grid(True)

    if x_axis_name:
        ax.set_xlabel(x_axis_name, fontsize=24)
    if y_axis_name:
        ax.set_ylabel(y_axis_name, fontsize=24)
    if title:
        ax.set_title(title, fontsize=28)

    ax.tick_params(axis="both", which="major", labelsize=18)
    ax.tick_params(axis="both", which="minor", labelsize=18)

    fig.savefig("s_curves.png", dpi=300, bbox_inches="tight")
    print("plotting")
    try:
        plt.tight_layout()
        plt.show()
    except:  # noqa
        pass  # noqa


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

    :param model_location: A directory containing model files ``.model``
    :param validation_set_location: A directory containing validation or test set points.
        These points should NOT be in the training set.
    :param atoms: A list of atom names, eg. O1, H2, C3, etc. for which to make S-curves.
        S-curves are made for all atoms in the system by default.
    :param types: A list of property types, such as iqa, q00, etc. for which to make S-curves.
        S-curves are made for all properties in the model files.
    :param kwargs: Any key word arguments that can be passed into the write_to_excel
        function to change how the S-curves excel file looks. See write_to_excel() method
    """

    if model_location is None or validation_set_location is None:
        raise ValueError("Enter valid locations for models and validation sets.")

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
    Writes out relevant information which is used to make s-curves to an excel file.
    It will make a separate sheet for every atom (and property). It
    also makes a ``Total`` sheet for every property, which gives
    an idea how the predictions do overall for the whole system.

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
    :param excel_style: The style which excel uses for the plots.
        Default is 10, which is the default style used by excel.
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
        for sheet_name in tqdm(
            true.keys(), desc="Writing S-curve sheets", total=len(true)
        ):

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

            # calculate a total df that sums up all the errors for
            # all atoms in one point and then sorts by error (ascending)
            # see ModelResult reduce method
            df = pd.DataFrame(error[sheet_name].reduce())
            df.rename(columns={0: "Total"}, inplace=True)
            df["Total"] = df["Total"].abs()
            df.sort_values("Total", inplace=True)
            ndata = len(df["Total"])
            df["%"] = percentile(ndata)
            # the end row is one more because the df starts one row down
            end_row = ndata + 1
            df.to_excel(writer, sheet_name=sheet_name, startrow=1, startcol=start_col)
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
