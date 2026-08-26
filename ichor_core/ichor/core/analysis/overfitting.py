"""Overfitting diagnostics for GPR models.

The quality metrics in :mod:`ichor.core.analysis.model_metrics` say how well a model
predicts a held-out set. They do not say whether a large held-out error is caused by
the model having memorised its training set, or by the held-out set simply covering
parts of configuration space the training set never visited. This module answers that
question with two checks.

**The generalisation gap.** The obvious comparison - training error against held-out
error - is useless for a GP: with the tiny jitter FEREBUS uses (1e-6 to 1e-10) the
model interpolates its own training data, so the training RMSE is at machine
precision whether the model generalises or not. The correct training-side estimate is
leave-one-out cross validation, which for a GP has a closed form that needs no
refitting (Rasmussen & Williams, eqs. 5.10-5.12)::

    loo_residual_i = [R^-1 (y - m)]_i / [R^-1]_ii
    loo_variance_i = tau^2 / [R^-1]_ii

Everything on the right hand side comes out of the ``.model`` file itself (the
training inputs ``x``, the training labels ``y``, the mean function and the kernel
hyperparameters), so no extra CSVs and no re-running of FEREBUS are needed. The ratio
``held-out RMSE / LOO RMSE`` is the generalisation gap.

**Uncertainty calibration.** A gap on its own is ambiguous, so it is read alongside
the predictive variance. Writing ``z = (y_true - y_predicted) / sigma``, a
well-calibrated GP has ``mean(z^2) ~ 1``. Then:

* large gap and large predictive variance on the held-out points - the held-out set
  lies outside the region the training set covers. The model knows it does not know,
  and the fix is more/better sampling rather than more regularisation.
* large gap and small predictive variance (``mean(z^2)`` well above 1) - the model is
  confidently wrong, which is overfitting proper.

``Model.variance`` returns the unnormalised ``1 - v^T v`` (see the TODO on it), so the
variances here are scaled by the signal variance ``tau^2`` estimated from the training
data by its maximum-likelihood value ``(y - m)^T R^-1 (y - m) / n``. This assumes the
kernel is a correlation kernel, i.e. ``k(x, x) = 1``, which holds for the RBF/periodic
compositions FEREBUS writes.

**A caveat worth knowing about.** The leave-one-out figures are derived from the
hyperparameters in the model file, whereas :meth:`Model.predict` (and therefore the
held-out figures, and FFLUX itself) uses the weights stored in the file. Those two
descriptions of the model should agree, because the stored weights should be exactly
``R^-1 (y - m)``. Every row of a report therefore carries a ``weights_mismatch``
column measuring how far apart they actually are; if it is large, the model file is
internally inconsistent and none of its predictions can be trusted, so the row is
diagnosed as ``inconsistent`` rather than being given a misleading verdict.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from ichor.core.analysis.model_metrics import (
    append_average_rows,
    ENERGY_PROPERTIES,
    metrics_from_true_predicted,
)
from ichor.core.common.constants import ha_to_kj_mol
from ichor.core.common.sorting import ignore_alpha
from ichor.core.common.str import get_characters
from ichor.core.models import Model, Models
from natsort import natsorted
from tqdm import tqdm

# a held-out RMSE more than this many times the leave-one-out RMSE is treated as a
# real generalisation gap rather than ordinary scatter between two finite samples
OVERFIT_RATIO_THRESHOLD = 2.0

# mean z^2 should be ~1 for a well calibrated GP. Outside this band the predictive
# uncertainties are not trustworthy: above it the model is over-confident (the
# signature of overfitting), below it needlessly pessimistic.
CALIBRATION_LOWER = 0.25
CALIBRATION_UPPER = 4.0

# if the mean predictive variance over the held-out points is more than this many
# times the mean leave-one-out variance, the held-out points sit outside the region
# the training set covers and the model is extrapolating rather than overfitting
COVERAGE_VARIANCE_RATIO = 2.0

# relative difference between the weights stored in a .model file and the weights its
# own hyperparameters imply, above which the file is treated as internally
# inconsistent. Solving the same linear system two different ways leaves a difference
# many orders of magnitude below this, so it only trips on a genuine disagreement.
WEIGHTS_MISMATCH_THRESHOLD = 1e-3

# variances at or below this are treated as zero when forming z-scores, so that
# numerically degenerate points do not produce infinite z
_MIN_VARIANCE = 1e-30

# values of the "diagnosis" column of an overfitting report
DIAGNOSIS_OK = "ok"
DIAGNOSIS_OVERFIT = "overfitting"
DIAGNOSIS_EXTRAPOLATION = "extrapolation"
DIAGNOSIS_MISCALIBRATED = "miscalibrated"
DIAGNOSIS_INCONSISTENT = "inconsistent"
DIAGNOSIS_UNCLEAR = "unclear"

# no percentile columns by default: an overfitting report is already wide, and the
# error percentiles are available from the quality-metrics report instead
DEFAULT_PERCENTILES: Sequence[int] = ()


@dataclass
class LeaveOneOutResult:
    """The outcome of a closed-form leave-one-out cross validation of one model.

    :param predicted: 1D array of leave-one-out predictions, one per training point,
        in the units of ``y``. Points whose covariance matrix diagonal came out
        non-positive (i.e. numerically not positive definite) are NaN.
    :param variance: 1D array of the variances of those predictions.
    :param signal_variance: the signal variance ``tau^2`` estimated from the training
        data. This is also the factor needed to put :meth:`Model.variance` on the
        scale of ``y`` squared, and is returned here so that the covariance matrix
        does not have to be inverted a second time to obtain it.
    :param weights_mismatch: the relative difference between the weights stored in the
        model file and the weights its hyperparameters imply, i.e.
        ``||w_stored - R^-1 (y - m)|| / ||R^-1 (y - m)||``. Should be ~0; a large
        value means the file is internally inconsistent. NaN if the file stored no
        weights.
    """

    predicted: np.ndarray
    variance: np.ndarray
    signal_variance: float
    weights_mismatch: float


def leave_one_out_predictions(model: Model) -> LeaveOneOutResult:
    """Computes closed-form leave-one-out cross validation predictions for a GP model,
    using only the data stored in its ``.model`` file. No refitting is done: the whole
    calculation is one inversion of the training covariance matrix.

    :param model: a ``Model`` whose training data (``x``, ``y``), mean function and
        kernel have been read from file.
    :return: a :class:`LeaveOneOutResult`.
    """

    y = np.asarray(model.y, dtype=float).reshape(-1, 1)
    n_train = y.shape[0]

    y_minus_mean = y - np.asarray(model.mean.value(model.x), dtype=float).reshape(-1, 1)

    inv_r = model.invR
    # alpha = R^-1 (y - m), the same quantity the model file stores as its weights
    alpha = inv_r @ y_minus_mean
    diag_inv_r = np.diag(inv_r).astype(float).copy()

    # maximum-likelihood signal variance for a GP written with a correlation kernel
    signal_variance = (y_minus_mean.T @ alpha).item() / n_train
    if not np.isfinite(signal_variance) or signal_variance <= 0.0:
        signal_variance = float("nan")

    # a non-positive diagonal means the covariance matrix was not positive definite
    # for that point, so its leave-one-out values are reported as missing rather than
    # as a nonsensical negative variance
    diag_inv_r[diag_inv_r <= 0.0] = np.nan

    loo_residual = alpha.flatten() / diag_inv_r
    loo_predicted = y.flatten() - loo_residual
    loo_variance = signal_variance / diag_inv_r

    return LeaveOneOutResult(
        predicted=loo_predicted,
        variance=loo_variance,
        signal_variance=signal_variance,
        weights_mismatch=weights_mismatch(model, alpha),
    )


def weights_mismatch(model: Model, implied_weights: np.ndarray) -> float:
    """Measures how far the weights stored in a model file are from the weights its
    own hyperparameters imply.

    :meth:`Model.predict` uses the stored weights, while every quantity derived from
    the kernel (the leave-one-out figures and the predictive variances) uses the
    hyperparameters. The two only describe the same model if the stored weights are
    ``R^-1 (y - m)``, so this is checked rather than assumed.

    :param model: the model whose stored weights are to be checked.
    :param implied_weights: ``R^-1 (y - m)`` computed from the model's hyperparameters.
    :return: ``||w_stored - implied|| / ||implied||``, or NaN if the file stored no
        weights or the implied weights are all zero.
    """

    if model.weights is None:
        return float("nan")

    stored = np.asarray(model.weights, dtype=float).reshape(-1, 1)
    implied = np.asarray(implied_weights, dtype=float).reshape(-1, 1)

    if stored.shape != implied.shape:
        return float("nan")

    implied_norm = np.linalg.norm(implied)
    if not np.isfinite(implied_norm) or implied_norm == 0.0:
        return float("nan")

    return float(np.linalg.norm(stored - implied) / implied_norm)


def predictive_variance(
    model: Model, x_test: np.ndarray, signal_variance: float
) -> np.ndarray:
    """Returns the predictive variance of ``model`` at ``x_test``, in the units of
    ``y`` squared.

    :meth:`Model.variance` returns the unnormalised ``1 - v^T v``, which is only
    useful for ranking points against each other, so it is multiplied here by the
    signal variance estimated from the training data.

    :param model: the model to predict with.
    :param x_test: a 2D array of test features.
    :param signal_variance: ``tau^2``, from :class:`LeaveOneOutResult`.
    :return: a 1D array of variances, one per test point.
    """

    # tiny negative values come out of the unnormalised variance for test points that
    # nearly coincide with a training point, so it is clipped at zero first
    unnormalised = np.maximum(np.asarray(model.variance(x_test), dtype=float), 0.0)

    return unnormalised * signal_variance


def calibration_metrics(
    true: np.ndarray, predicted: np.ndarray, variance: np.ndarray
) -> dict:
    """Computes how well the model's predictive uncertainties match its actual errors.

    :param true: 1D array of reference values.
    :param predicted: 1D array of predictions.
    :param variance: 1D array of predictive variances, in the units of ``true``
        squared.
    :return: a dict with ``mean_z2`` (the mean squared error divided by the predicted
        variance, which should be ~1), ``frac_within_95`` (the fraction of points
        inside their 95% predictive interval, which should be ~0.95) and
        ``mean_predictive_std`` (the mean predictive standard deviation, in the units
        of ``true``). All are NaN if no point has a usable variance.
    """

    residual = np.asarray(true, dtype=float) - np.asarray(predicted, dtype=float)
    variance = np.asarray(variance, dtype=float)

    usable = np.isfinite(residual) & np.isfinite(variance) & (variance > _MIN_VARIANCE)
    if not usable.any():
        return {
            "mean_z2": float("nan"),
            "frac_within_95": float("nan"),
            "mean_predictive_std": float("nan"),
        }

    standard_deviation = np.sqrt(variance[usable])
    z = residual[usable] / standard_deviation

    return {
        "mean_z2": float(np.mean(z**2)),
        "frac_within_95": float(np.mean(np.abs(z) < 1.96)),
        "mean_predictive_std": float(np.mean(standard_deviation)),
    }


def diagnose(
    overfit_ratio: float,
    held_out_mean_z2: float,
    variance_ratio: float,
    mismatch: float = float("nan"),
) -> str:
    """Turns the numbers of an overfitting report row into a one-word verdict.

    :param overfit_ratio: held-out RMSE divided by leave-one-out RMSE.
    :param held_out_mean_z2: mean z^2 over the held-out points.
    :param variance_ratio: mean predictive variance over the held-out points divided
        by the mean leave-one-out variance.
    :param mismatch: the model's ``weights_mismatch``.
    :return: one of the ``DIAGNOSIS_*`` constants of this module.
    """

    # nothing else in the row means anything if the file disagrees with itself, since
    # the two sides of the comparison would then describe two different models
    if np.isfinite(mismatch) and mismatch > WEIGHTS_MISMATCH_THRESHOLD:
        return DIAGNOSIS_INCONSISTENT

    if not np.isfinite(overfit_ratio):
        return DIAGNOSIS_UNCLEAR

    if overfit_ratio <= OVERFIT_RATIO_THRESHOLD:
        # the model generalises, but its error bars may still be the wrong size
        if np.isfinite(held_out_mean_z2) and not (
            CALIBRATION_LOWER <= held_out_mean_z2 <= CALIBRATION_UPPER
        ):
            return DIAGNOSIS_MISCALIBRATED
        return DIAGNOSIS_OK

    # from here on the held-out error is much worse than leave-one-out suggests

    # the model reports much larger uncertainty on the held-out points than on its own
    # training points, i.e. it is being asked about parts of configuration space the
    # training set does not cover. That is a sampling problem, not overfitting.
    if np.isfinite(variance_ratio) and variance_ratio > COVERAGE_VARIANCE_RATIO:
        return DIAGNOSIS_EXTRAPOLATION

    # confidently wrong: large errors that the model's own uncertainty did not predict
    if np.isfinite(held_out_mean_z2) and held_out_mean_z2 > CALIBRATION_UPPER:
        return DIAGNOSIS_OVERFIT

    return DIAGNOSIS_UNCLEAR


# columns that are only filled in when a held-out set was supplied
_HELD_OUT_COLUMNS = (
    "heldout_rmse",
    "heldout_mae",
    "heldout_r2",
    "heldout_max_error",
    "overfit_ratio",
    "heldout_mean_z2",
    "heldout_frac_within_95",
    "heldout_mean_predictive_std",
    "variance_ratio",
)


def overfitting_row_for_model(
    model: Model,
    held_out_features: Optional[np.ndarray] = None,
    held_out_true: Optional[np.ndarray] = None,
    split_name: str = "",
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> dict:
    """Builds one row of an overfitting report for a single model.

    :param model: the model to check.
    :param held_out_features: 2D array of features of the held-out points. If ``None``,
        only the leave-one-out columns are filled in.
    :param held_out_true: 1D array of reference values for the held-out points.
    :param split_name: name of the held-out split, recorded in the ``split`` column.
    :param percentiles: percentiles of the absolute error to add to the report.
    :return: a dict of column name -> value.
    """

    is_energy = model.prop in ENERGY_PROPERTIES
    # energies are predicted in Hartrees but reported in kJ mol-1
    error_scale = ha_to_kj_mol if is_energy else 1.0
    units = "kJ mol-1" if is_energy else "atomic units"

    loo = leave_one_out_predictions(model)
    y_train = np.asarray(model.y, dtype=float).flatten()

    row = {
        "property": model.prop,
        "atom": model.atom_name,
        "element": get_characters(model.atom_name),
        "units": units,
        "split": split_name,
        "ntrain": int(model.ntrain),
        "weights_mismatch": loo.weights_mismatch,
    }

    # the training error is reported for contrast only: a healthy GP interpolates its
    # own training data, so this should be near zero and says nothing about
    # generalisation. A large value means the model is not reproducing the data it was
    # fitted to, which points at the model file rather than at overfitting.
    train_metrics = metrics_from_true_predicted(
        y_train, model.predict(model.x), percentiles=(), error_scale=error_scale
    )
    row["train_rmse"] = train_metrics["rmse"]

    # leave-one-out points with a non-positive covariance diagonal are dropped so a
    # single ill-conditioned point cannot turn the whole row into NaN
    finite_loo = np.isfinite(loo.predicted)
    if finite_loo.any():
        loo_metrics = metrics_from_true_predicted(
            y_train[finite_loo],
            loo.predicted[finite_loo],
            percentiles=percentiles,
            error_scale=error_scale,
        )
        loo_calibration = calibration_metrics(
            y_train[finite_loo], loo.predicted[finite_loo], loo.variance[finite_loo]
        )
        mean_loo_variance = float(np.nanmean(loo.variance[finite_loo]))
    else:
        loo_metrics = {"rmse": float("nan"), "mae": float("nan"), "r2": float("nan")}
        loo_calibration = {"mean_z2": float("nan")}
        mean_loo_variance = float("nan")

    row["loo_rmse"] = loo_metrics["rmse"]
    row["loo_mae"] = loo_metrics["mae"]
    row["loo_r2"] = loo_metrics["r2"]
    row["loo_mean_z2"] = loo_calibration["mean_z2"]

    if held_out_features is None or held_out_true is None:
        row["heldout_n"] = 0
        for column in _HELD_OUT_COLUMNS:
            row[column] = float("nan")
        row["diagnosis"] = diagnose(
            float("nan"), float("nan"), float("nan"), loo.weights_mismatch
        )
        return row

    held_out_predicted = model.predict(held_out_features)
    held_out_variance = predictive_variance(
        model, held_out_features, loo.signal_variance
    )

    held_out_metrics = metrics_from_true_predicted(
        held_out_true,
        held_out_predicted,
        percentiles=percentiles,
        error_scale=error_scale,
    )
    held_out_calibration = calibration_metrics(
        held_out_true, held_out_predicted, held_out_variance
    )

    row["heldout_n"] = held_out_metrics["n_points"]
    row["heldout_rmse"] = held_out_metrics["rmse"]
    row["heldout_mae"] = held_out_metrics["mae"]
    row["heldout_r2"] = held_out_metrics["r2"]
    row["heldout_max_error"] = held_out_metrics["max_error"]

    # the generalisation gap. Both RMSEs carry the same error_scale, so it cancels.
    loo_rmse = row["loo_rmse"]
    row["overfit_ratio"] = (
        held_out_metrics["rmse"] / loo_rmse
        if np.isfinite(loo_rmse) and loo_rmse > 0.0
        else float("nan")
    )

    row["heldout_mean_z2"] = held_out_calibration["mean_z2"]
    row["heldout_frac_within_95"] = held_out_calibration["frac_within_95"]
    # the standard deviations are in the units of y, so they take the same scaling as
    # the other error-magnitude columns
    row["heldout_mean_predictive_std"] = (
        held_out_calibration["mean_predictive_std"] * error_scale
    )

    # how much less the model knows about the held-out points than about its own
    # training points, which is what separates extrapolation from overfitting
    mean_held_out_variance = float(np.nanmean(held_out_variance))
    row["variance_ratio"] = (
        mean_held_out_variance / mean_loo_variance
        if np.isfinite(mean_loo_variance) and mean_loo_variance > 0.0
        else float("nan")
    )

    row["diagnosis"] = diagnose(
        row["overfit_ratio"],
        row["heldout_mean_z2"],
        row["variance_ratio"],
        loo.weights_mismatch,
    )

    return row


def overfitting_report(
    models: Models,
    csv_files_list: Optional[List[Union[str, Path]]] = None,
    split_name: str = "",
    output_location: Optional[Union[str, Path]] = "overfitting_report.csv",
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> pd.DataFrame:
    """Checks a set of models for overfitting and (optionally) writes the report to a
    CSV file.

    Each model is compared against itself through closed-form leave-one-out cross
    validation on its own training data, and against the held-out split given by
    ``csv_files_list``. See the module docstring for how to read the resulting
    ``overfit_ratio``, ``heldout_mean_z2`` and ``variance_ratio`` columns.

    :param models: a ``Models`` instance containing the ``.model`` files.
    :param csv_files_list: FEREBUS/ichor per-(atom, property) CSVs of a single
        held-out split (e.g. only the EXT_VALIDATION_SET files). If ``None`` or empty,
        only the leave-one-out columns are computed.
    :param split_name: name of the held-out split, recorded in the ``split`` column.
    :param output_location: path of the CSV file to write the report to. If ``None``,
        no file is written and the DataFrame is only returned.
    :param percentiles: percentiles of the absolute error to add to the report.
    :return: the report DataFrame, one row per (atom, property).
    """

    # imported lazily to avoid any package-initialisation ordering issues
    from ichor.core.analysis.s_curves.compact_s_curves import (
        ferebus_csv_index,
        match_model_to_csv_key,
    )

    csv_index = ferebus_csv_index(csv_files_list) if csv_files_list else {}

    rows = []
    for model in tqdm(models, desc="Checking for overfitting"):
        key = match_model_to_csv_key(csv_index, model.atom_name, model.prop)
        features, true_values = csv_index[key] if key is not None else (None, None)

        rows.append(
            overfitting_row_for_model(
                model,
                held_out_features=features,
                held_out_true=true_values,
                split_name=split_name,
                percentiles=percentiles,
            )
        )

    report_df = pd.DataFrame(rows)

    if not report_df.empty:
        # group the rows by property and put each property's atoms in natural order
        # (O1, H2, H3, ... rather than H2, H3, O1) to match the other reports
        atom_order = natsorted(report_df["atom"].unique(), key=ignore_alpha)
        report_df = (
            report_df.assign(
                _atom_order=[atom_order.index(atom) for atom in report_df["atom"]]
            )
            .sort_values(["property", "_atom_order"])
            .drop(columns="_atom_order")
            .reset_index(drop=True)
        )

    if output_location is not None:
        append_average_rows(report_df).to_csv(output_location, index=False)

    return report_df


def summarise_diagnoses(report_df: pd.DataFrame) -> str:
    """Builds a short human-readable summary of an overfitting report, listing how
    many models fell into each diagnosis and naming the worst offenders.

    :param report_df: a report as returned by :func:`overfitting_report`.
    :return: a multi-line summary string.
    """

    if report_df.empty or "diagnosis" not in report_df.columns:
        return "No models were checked."

    lines = [f"{len(report_df)} model(s) checked:"]
    counts = report_df["diagnosis"].value_counts()
    for diagnosis in (
        DIAGNOSIS_OK,
        DIAGNOSIS_OVERFIT,
        DIAGNOSIS_EXTRAPOLATION,
        DIAGNOSIS_MISCALIBRATED,
        DIAGNOSIS_INCONSISTENT,
        DIAGNOSIS_UNCLEAR,
    ):
        if diagnosis in counts:
            lines.append(f"  {counts[diagnosis]:>4}  {diagnosis}")

    if DIAGNOSIS_INCONSISTENT in counts:
        lines.append(
            "\n'inconsistent' means the weights stored in the model file do not match "
            "the weights\nits own hyperparameters imply, so its predictions cannot be "
            "trusted and no overfitting\nverdict was attempted. Check how those files "
            "were written."
        )

    overfit = report_df[report_df["diagnosis"] == DIAGNOSIS_OVERFIT]
    if not overfit.empty:
        worst = overfit.nlargest(min(5, len(overfit)), "overfit_ratio")
        lines.append(
            "\nWorst generalisation gaps (held-out RMSE / leave-one-out RMSE):"
        )
        for _, r in worst.iterrows():
            lines.append(
                f"  {r['property']:<12} {r['atom']:<6} "
                f"ratio {r['overfit_ratio']:.1f}, mean z^2 {r['heldout_mean_z2']:.1f}"
            )

    return "\n".join(lines)
