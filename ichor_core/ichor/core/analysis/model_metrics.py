"""Compute scalar quality metrics (RMSE, MAE, R2, max error and error
percentiles) for GPR models, given a validation/test set. These complement
the S-curves in :mod:`ichor.core.analysis.s_curves` by giving single numbers
that summarise how well each atom/property model predicts."""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from ichor.core.analysis.predictions import get_true_predicted
from ichor.core.common.constants import ha_to_kj_mol
from ichor.core.common.str import get_characters
from ichor.core.files import PointsDirectory
from ichor.core.models import Models
from tqdm import tqdm

# properties whose prediction errors are reported in kJ mol-1 (they are
# predicted in Hartrees, so the errors are converted before computing metrics)
ENERGY_PROPERTIES = ("iqa", "iqa_energy", "wfn_energy")

DEFAULT_PERCENTILES = (90, 95, 99)

# identifier columns in a metrics table; everything else is a numeric metric that
# is averaged when building the average row(s)
_METRIC_ID_COLUMNS = ("property", "atom", "element", "units")


def append_average_rows(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of ``metrics_df`` with an average row appended for each
    property (its metrics averaged over that property's atoms). A row is added per
    property rather than a single one, because different properties are reported in
    different units (kJ mol-1 vs atomic units) and so must not be averaged together.
    The average rows are labelled with ``atom = "AVERAGE"`` and placed at the end.

    :param metrics_df: a metrics table with the identifier columns in
        ``_METRIC_ID_COLUMNS`` plus numeric metric columns.
    :return: the table with the average row(s) appended (unchanged if empty).
    """

    if metrics_df.empty:
        return metrics_df

    metric_cols = [c for c in metrics_df.columns if c not in _METRIC_ID_COLUMNS]

    avg_rows = []
    # sort=False keeps the properties in their existing (already sorted) order
    for property_name, group in metrics_df.groupby("property", sort=False):
        row = {"property": property_name, "atom": "AVERAGE"}
        if "element" in metrics_df.columns:
            elements = group["element"].unique()
            row["element"] = elements[0] if len(elements) == 1 else "ALL"
        if "units" in metrics_df.columns:
            units = group["units"].unique()
            row["units"] = units[0] if len(units) == 1 else ""
        for col in metric_cols:
            row[col] = group[col].mean()
        avg_rows.append(row)

    return pd.concat([metrics_df, pd.DataFrame(avg_rows)], ignore_index=True)


def metrics_from_true_predicted(
    true: np.ndarray,
    predicted: np.ndarray,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
    error_scale: float = 1.0,
) -> dict:
    """Computes quality metrics for a single 1D array of true values and the
    corresponding array of predicted values.

    :param true: 1D array of reference (e.g. AIMAll) values.
    :param predicted: 1D array of model-predicted values, same length as ``true``.
    :param percentiles: percentiles of the absolute error to report, e.g. (90, 95, 99).
    :param error_scale: a factor the raw errors are multiplied by so that the
        error-magnitude metrics (RMSE, MAE, max error, percentiles) are in the
        desired units (e.g. ``ha_to_kj_mol`` for energies). R2 is dimensionless
        and unaffected by this scale.
    :return: a dictionary of metric name -> value.
    """

    true = np.asarray(true, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    raw_errors = true - predicted
    # scaled errors are used for all error-magnitude metrics so they come out
    # in the requested units
    errors = raw_errors * error_scale
    abs_errors = np.abs(errors)
    n_points = abs_errors.shape[0]

    rmse = float(np.sqrt(np.mean(errors**2)))
    mae = float(np.mean(abs_errors))
    max_error = float(np.max(abs_errors))

    # R2 (coefficient of determination). It is scale invariant, so it is
    # computed from the raw errors and raw true values.
    ss_res = float(np.sum(raw_errors**2))
    ss_tot = float(np.sum((true - np.mean(true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0.0 else float("nan")

    metrics = {
        "n_points": n_points,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "max_error": max_error,
    }
    for p in percentiles:
        metrics[f"p{p}_abs_error"] = float(np.percentile(abs_errors, p))

    return metrics


def calculate_metrics_dataframe(
    true: pd.DataFrame,
    predicted: pd.DataFrame,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> pd.DataFrame:
    """Builds a tidy metrics table (one row per atom/property) from the ``true``
    and ``predicted`` dataframes returned by
    :func:`ichor.core.analysis.predictions.get_true_predicted`.

    :param true: DataFrame of true values (columns are atom names, index are
        property types, each cell a 1D array over points).
    :param predicted: DataFrame of predicted values, same layout as ``true``.
    :param percentiles: percentiles of the absolute error to report.
    :return: a DataFrame with columns ``property``, ``atom``, ``units``,
        ``n_points``, ``rmse``, ``mae``, ``r2``, ``max_error`` and one column
        per requested percentile.
    """

    # transpose so that iterating over columns iterates over property types,
    # matching the convention used in the s_curves module
    true = true.T
    predicted = predicted.T

    rows = []
    for type_ in tqdm(sorted(true.keys()), desc="Computing metrics"):
        atom_names = true[type_].keys()
        is_energy = type_ in ENERGY_PROPERTIES
        error_scale = ha_to_kj_mol if is_energy else 1.0
        units = "kJ mol-1" if is_energy else "atomic units"

        for atom in atom_names:
            metrics = metrics_from_true_predicted(
                true[type_][atom],
                predicted[type_][atom],
                percentiles=percentiles,
                error_scale=error_scale,
            )
            rows.append(
                {
                    "property": type_,
                    "atom": atom,
                    "element": get_characters(atom),
                    "units": units,
                    **metrics,
                }
            )

    return pd.DataFrame(rows)


def calculate_model_metrics(
    model_location: Union[str, Path],
    validation_set_location: Union[str, Path],
    output_location: Optional[Union[str, Path]] = "model_metrics.csv",
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> pd.DataFrame:
    """Computes quality metrics for a set of models against a validation/test set
    and (optionally) writes them to a CSV file.

    :param model_location: A directory containing model files ``.model``.
    :param validation_set_location: A directory (``PointsDirectory``) containing
        validation or test set points. These should NOT be in the training set.
    :param output_location: Path of the CSV file to write the metrics to. If
        ``None``, no file is written and the DataFrame is only returned.
    :param atoms: Optional list of atom names, e.g. O1, H2, C3. Defaults to all
        atoms found in the models.
    :param types: Optional list of property types, e.g. iqa, q00. Defaults to all
        property types found in the models.
    :param percentiles: Percentiles of the absolute error to report.
    :return: The metrics DataFrame (also written to ``output_location``).
    """

    if model_location is None or validation_set_location is None:
        raise ValueError("Enter valid locations for models and validation sets.")

    models = Models(model_location)
    validation_set = PointsDirectory(validation_set_location)
    true, predicted = get_true_predicted(models, validation_set, atoms, types)

    metrics_df = calculate_metrics_dataframe(true, predicted, percentiles=percentiles)

    if output_location is not None:
        append_average_rows(metrics_df).to_csv(output_location, index=False)

    return metrics_df


def calculate_metrics_from_csv_files(
    csv_files_list: List[Union[str, Path]],
    models: "Models",
    output_location: Optional[Union[str, Path]] = "model_metrics.csv",
    property_names: Optional[List[str]] = None,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> pd.DataFrame:
    """Computes quality metrics from a set of per-atom CSV files (features + true
    values, as produced by the ichor/polus data-prep step) and a set of models.
    This is the natural path for evaluating models against a held-out test/valid
    split, since those splits are stored as CSVs rather than as a PointsDirectory.

    :param csv_files_list: A list of per-atom .csv files containing feature columns
        and property columns. The atom name is taken from the part of each file
        name before the first underscore.
    :param models: A ``Models`` instance containing the ``.model`` files.
    :param output_location: Path of the CSV file to write the metrics to. If
        ``None``, no file is written and the DataFrame is only returned.
    :param property_names: Optional list of property column names to read. Defaults
        to iqa, wfn_energy and the multipole moments.
    :param percentiles: Percentiles of the absolute error to report.
    :return: The metrics DataFrame (also written to ``output_location``).
    """

    # imported lazily to avoid any package-initialisation ordering issues
    from ichor.core.analysis.s_curves.compact_s_curves import (
        true_predicted_dict_from_csv_files,
    )

    total_dict, _ = true_predicted_dict_from_csv_files(
        csv_files_list, models, property_names
    )

    return metrics_df_from_total_dict(
        total_dict, percentiles=percentiles, output_location=output_location
    )


def metrics_df_from_total_dict(
    total_dict: dict,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
    output_location: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Builds a tidy metrics table from a nested ``total_dict`` of the form
    ``{property: {atom: {"true", "predicted", ...}}}`` (as produced by the CSV
    readers in :mod:`ichor.core.analysis.s_curves.compact_s_curves`).

    :param total_dict: nested dict keyed by property then atom, each holding
        ``"true"`` and ``"predicted"`` 1D arrays.
    :param percentiles: percentiles of the absolute error to report.
    :param output_location: if not ``None``, the metrics are written to this CSV.
    :return: the metrics DataFrame.
    """

    rows = []
    for type_ in tqdm(sorted(total_dict.keys()), desc="Computing metrics"):
        is_energy = type_ in ENERGY_PROPERTIES
        error_scale = ha_to_kj_mol if is_energy else 1.0
        units = "kJ mol-1" if is_energy else "atomic units"

        for atom in total_dict[type_].keys():
            atom_data = total_dict[type_][atom]
            metrics = metrics_from_true_predicted(
                atom_data["true"],
                atom_data["predicted"],
                percentiles=percentiles,
                error_scale=error_scale,
            )
            rows.append(
                {
                    "property": type_,
                    "atom": atom,
                    "element": get_characters(atom),
                    "units": units,
                    **metrics,
                }
            )

    metrics_df = pd.DataFrame(rows)

    if output_location is not None:
        append_average_rows(metrics_df).to_csv(output_location, index=False)

    return metrics_df


def write_metrics_per_element(
    metrics_df: pd.DataFrame,
    output_location: Union[str, Path],
) -> List[Path]:
    """Writes a separate metrics CSV for each element type, inserting the element
    symbol into the file name, e.g. ``model_metrics.csv`` ->
    ``model_metrics_C.csv``, ``model_metrics_H.csv``, ``model_metrics_O.csv``.

    :param metrics_df: a metrics table as produced by
        :func:`metrics_df_from_total_dict` or :func:`calculate_metrics_dataframe`.
        If it has no ``element`` column, one is derived from the ``atom`` column.
    :param output_location: base CSV path; the element symbol is inserted before
        the extension for each written file.
    :return: the list of CSV paths that were written (natsorted by element).
    """

    from natsort import natsorted

    if metrics_df.empty:
        return []

    if "element" not in metrics_df.columns:
        metrics_df = metrics_df.assign(
            element=metrics_df["atom"].map(get_characters)
        )

    base_path = Path(output_location)
    written: List[Path] = []
    for element in natsorted(metrics_df["element"].unique()):
        element_df = metrics_df[metrics_df["element"] == element]
        out_path = base_path.with_name(
            f"{base_path.stem}_{element}{base_path.suffix}"
        )
        append_average_rows(element_df).to_csv(out_path, index=False)
        written.append(out_path)

    return written


def calculate_metrics_from_ferebus_csvs(
    csv_files_list: List[Union[str, Path]],
    models: "Models",
    output_location: Optional[Union[str, Path]] = "model_metrics.csv",
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> pd.DataFrame:
    """Computes quality metrics from FEREBUS/ichor per-(atom, property) training-style
    CSVs (feature columns ``f1..fN`` plus one property column) and a set of models.
    This is the natural path for evaluating models stored in ``6_MODELS`` against
    their held-out EXT_VALIDATION (external) or INT_VALIDATION (internal) split.

    :param csv_files_list: A list of per-(atom, property) CSV files, all of a single
        held-out split (e.g. only the EXT_VALIDATION_SET files).
    :param models: A ``Models`` instance containing the ``.model`` files.
    :param output_location: Path of the CSV file to write the metrics to. If
        ``None``, no file is written and the DataFrame is only returned.
    :param percentiles: Percentiles of the absolute error to report.
    :return: The metrics DataFrame (also written to ``output_location``).
    """

    # imported lazily to avoid any package-initialisation ordering issues
    from ichor.core.analysis.s_curves.compact_s_curves import (
        true_predicted_from_ferebus_csvs,
    )

    total_dict = true_predicted_from_ferebus_csvs(csv_files_list, models)

    return metrics_df_from_total_dict(
        total_dict, percentiles=percentiles, output_location=output_location
    )


def get_true_predicted_dicts(
    model_location: Union[str, Path],
    validation_set_location: Union[str, Path],
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
) -> Tuple[dict, dict]:
    """Convenience helper returning ``true`` and ``predicted`` values as nested
    dictionaries of the form ``{atom_name: {property: 1D array}}``. This is the
    format consumed by the matplotlib plotting helpers in
    :mod:`ichor.core.analysis.s_curves.compact_s_curves`.

    :param model_location: A directory containing model files ``.model``.
    :param validation_set_location: A ``PointsDirectory`` of validation/test points.
    :param atoms: Optional list of atom names to restrict to.
    :param types: Optional list of property types to restrict to.
    :return: a tuple ``(true_dict, predicted_dict)``.
    """

    models = Models(model_location)
    validation_set = PointsDirectory(validation_set_location)
    true, predicted = get_true_predicted(models, validation_set, atoms, types)

    # DataFrame columns are atom names and the index is the property type, so
    # ``to_dict`` yields {atom_name: {property: array}}
    return true.to_dict(), predicted.to_dict()
