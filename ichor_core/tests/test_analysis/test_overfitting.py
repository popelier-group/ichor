"""Tests for the overfitting diagnostics in :mod:`ichor.core.analysis.overfitting`.

The models used here are built by hand rather than read from FEREBUS output, so that
the training data, the kernel and the weights are known to be consistent with each
other and the closed-form leave-one-out result can be checked against brute force.
"""

import numpy as np
import pytest
from ichor.core.analysis.overfitting import (
    calibration_metrics,
    diagnose,
    DIAGNOSIS_EXTRAPOLATION,
    DIAGNOSIS_INCONSISTENT,
    DIAGNOSIS_MISCALIBRATED,
    DIAGNOSIS_OK,
    DIAGNOSIS_OVERFIT,
    DIAGNOSIS_UNCLEAR,
    leave_one_out_predictions,
    overfitting_report,
    overfitting_row_for_model,
    predictive_variance,
)
from ichor.core.models import Model
from ichor.core.models.kernels import RBF
from ichor.core.models.mean import ConstantMean

N_TRAIN = 60
N_FEATURES = 3
JITTER = 1e-8


def smooth_function(x: np.ndarray) -> np.ndarray:
    """A smooth function of the features, standing in for an IQA energy surface."""
    return np.sin(3 * x[:, 0]) + 0.5 * x[:, 1] ** 2 - x[:, 2]


def make_model(tmp_path, property_name: str = "q00", seed: int = 1) -> Model:
    """Builds a GP model whose stored weights are exactly ``R^-1 (y - m)``, i.e. one
    that is internally consistent."""

    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, (N_TRAIN, N_FEATURES))
    y = smooth_function(x).reshape(-1, 1)

    kernel = RBF("k1", np.ones(N_FEATURES), active_dims=np.arange(N_FEATURES))
    mean = ConstantMean(float(y.mean()))

    covariance = kernel.R(x) + JITTER * np.identity(N_TRAIN)
    weights = np.linalg.solve(covariance, y - mean.value(x).reshape(-1, 1))

    path = tmp_path / f"SYS_{property_name}_O1.model"
    path.touch()

    return Model(
        path,
        system_name="SYS",
        atom_name="O1",
        prop=property_name,
        alf=None,
        natoms=1,
        ntrain=N_TRAIN,
        nfeats=N_FEATURES,
        mean=mean,
        kernel=kernel,
        x=x,
        y=y,
        input_units=["bohr"] * N_FEATURES,
        output_unit="e",
        likelihood=1.0,
        jitter=JITTER,
        weights=weights,
        program="test",
        program_version=None,
        notes={},
    )


def brute_force_leave_one_out(model: Model, index: int):
    """Refits the GP with one training point removed and predicts at that point,
    returning ``(prediction, variance)``. This is what the closed form must reproduce."""

    covariance = model.kernel.R(model.x) + model.jitter * np.identity(model.ntrain)
    mean_values = np.asarray(model.mean.value(model.x), dtype=float).flatten()
    y = np.asarray(model.y, dtype=float).flatten()

    kept = np.array([i for i in range(model.ntrain) if i != index])
    covariance_kept = covariance[np.ix_(kept, kept)]
    cross_covariance = covariance[np.ix_(kept, [index])]

    y_minus_mean = (y[kept] - mean_values[kept]).reshape(-1, 1)
    prediction = (
        mean_values[index]
        + (cross_covariance.T @ np.linalg.solve(covariance_kept, y_minus_mean)).item()
    )
    variance = (
        covariance[index, index]
        - (
            cross_covariance.T @ np.linalg.solve(covariance_kept, cross_covariance)
        ).item()
    )

    return prediction, variance


def test_leave_one_out_matches_brute_force(tmp_path):
    """The closed-form leave-one-out result must equal an explicit refit."""

    model = make_model(tmp_path)
    loo = leave_one_out_predictions(model)

    for index in (0, 7, 23, N_TRAIN - 1):
        prediction, variance = brute_force_leave_one_out(model, index)
        assert loo.predicted[index] == pytest.approx(prediction, abs=1e-8)
        # the closed form carries the signal variance, the brute force does not
        assert loo.variance[index] == pytest.approx(
            loo.signal_variance * variance, rel=1e-6
        )


def test_leave_one_out_is_worse_than_training_error(tmp_path):
    """A GP interpolates its own training data, so the training error says nothing.
    Leave-one-out must give a meaningfully larger, i.e. honest, error."""

    model = make_model(tmp_path)
    y = np.asarray(model.y, dtype=float).flatten()

    train_rmse = np.sqrt(np.mean((y - model.predict(model.x)) ** 2))
    loo = leave_one_out_predictions(model)
    loo_rmse = np.sqrt(np.mean((y - loo.predicted) ** 2))

    assert train_rmse < 1e-4
    assert loo_rmse > 10 * train_rmse


def test_consistent_model_has_no_weights_mismatch(tmp_path):
    """A model whose weights were built from its own hyperparameters agrees with
    itself."""

    loo = leave_one_out_predictions(make_model(tmp_path))
    assert loo.weights_mismatch < 1e-8


def test_tampered_weights_are_reported_as_inconsistent(tmp_path):
    """If the stored weights do not match the hyperparameters, the model file cannot
    be trusted and no overfitting verdict should be attempted."""

    model = make_model(tmp_path)
    model.weights = model.weights * 0.5

    loo = leave_one_out_predictions(model)
    assert loo.weights_mismatch == pytest.approx(0.5, rel=1e-6)

    rng = np.random.default_rng(9)
    x_test = rng.uniform(0.0, 1.0, (30, N_FEATURES))
    row = overfitting_row_for_model(model, x_test, smooth_function(x_test))
    assert row["diagnosis"] == DIAGNOSIS_INCONSISTENT


def test_signal_variance_scales_predictive_variance(tmp_path):
    """The scaled predictive variance is the unnormalised one times tau^2, and is
    near zero at the training points themselves."""

    model = make_model(tmp_path)
    loo = leave_one_out_predictions(model)

    variance = predictive_variance(model, model.x, loo.signal_variance)
    assert np.all(variance >= 0.0)
    assert np.max(variance) < 1e-6 * loo.signal_variance

    rng = np.random.default_rng(3)
    x_far = rng.uniform(5.0, 6.0, (10, N_FEATURES))
    # far from any training point the model falls back on the prior variance, tau^2
    assert np.mean(predictive_variance(model, x_far, loo.signal_variance)) == (
        pytest.approx(loo.signal_variance, rel=1e-3)
    )


def test_calibration_metrics_on_known_z_scores():
    """Errors of exactly one standard deviation give mean z^2 of one."""

    true = np.array([1.0, 2.0, 3.0, 4.0])
    predicted = true - 0.5
    variance = np.full(4, 0.25)  # standard deviation 0.5

    metrics = calibration_metrics(true, predicted, variance)
    assert metrics["mean_z2"] == pytest.approx(1.0)
    assert metrics["frac_within_95"] == pytest.approx(1.0)
    assert metrics["mean_predictive_std"] == pytest.approx(0.5)


def test_calibration_metrics_without_usable_variance():
    """Zero variances cannot produce z-scores and must not raise or divide by zero."""

    metrics = calibration_metrics(
        np.array([1.0, 2.0]), np.array([1.0, 2.0]), np.zeros(2)
    )
    assert np.isnan(metrics["mean_z2"])
    assert np.isnan(metrics["frac_within_95"])


@pytest.mark.parametrize(
    "overfit_ratio, mean_z2, variance_ratio, mismatch, expected",
    [
        (1.2, 1.0, 1.0, 0.0, DIAGNOSIS_OK),
        # a small gap but error bars of the wrong size
        (1.2, 50.0, 1.0, 0.0, DIAGNOSIS_MISCALIBRATED),
        # big gap, and the model said it was uncertain about the held-out points
        (50.0, 3.0, 100.0, 0.0, DIAGNOSIS_EXTRAPOLATION),
        # big gap that the model's own uncertainty did not anticipate
        (50.0, 500.0, 1.0, 0.0, DIAGNOSIS_OVERFIT),
        # an inconsistent file overrides everything else
        (1.2, 1.0, 1.0, 0.5, DIAGNOSIS_INCONSISTENT),
        (float("nan"), 1.0, 1.0, 0.0, DIAGNOSIS_UNCLEAR),
    ],
)
def test_diagnose(overfit_ratio, mean_z2, variance_ratio, mismatch, expected):
    assert diagnose(overfit_ratio, mean_z2, variance_ratio, mismatch) == expected


def test_report_distinguishes_extrapolation_from_overfitting(tmp_path):
    """The end-to-end check on three held-out sets which differ only in how they were
    drawn: from the training region, from far outside it, and from the training region
    but with a systematic shift the model cannot know about."""

    model = make_model(tmp_path)
    rng = np.random.default_rng(11)

    x_same = rng.uniform(0.0, 1.0, (40, N_FEATURES))
    same_region = overfitting_row_for_model(model, x_same, smooth_function(x_same))

    x_far = rng.uniform(2.0, 3.0, (40, N_FEATURES))
    far_away = overfitting_row_for_model(model, x_far, smooth_function(x_far))

    x_shifted = rng.uniform(0.0, 1.0, (40, N_FEATURES))
    shifted = overfitting_row_for_model(
        model, x_shifted, smooth_function(x_shifted) + 0.5
    )

    assert same_region["diagnosis"] == DIAGNOSIS_OK
    assert same_region["overfit_ratio"] < 2.0

    # far outside the training region the model knows it does not know: its predictive
    # variance rises far more than its error does relative to leave-one-out
    assert far_away["diagnosis"] == DIAGNOSIS_EXTRAPOLATION
    assert far_away["variance_ratio"] > 10.0

    # in the training region the model is confident, so the same size of error is a
    # much more serious finding
    assert shifted["diagnosis"] == DIAGNOSIS_OVERFIT
    assert shifted["variance_ratio"] < 2.0
    assert shifted["heldout_mean_z2"] > 4.0


def test_overfitting_report_without_held_out_set(tmp_path):
    """With no held-out CSVs the leave-one-out columns are still filled in, and the
    verdict is withheld rather than guessed."""

    models = [make_model(tmp_path, property_name="q00")]
    output = tmp_path / "overfitting_report.csv"

    report = overfitting_report(models, csv_files_list=None, output_location=output)

    assert len(report) == 1
    row = report.iloc[0]
    assert row["heldout_n"] == 0
    assert np.isfinite(row["loo_rmse"])
    assert np.isnan(row["overfit_ratio"])
    assert row["diagnosis"] == DIAGNOSIS_UNCLEAR
    assert output.is_file()


def test_report_columns_and_units(tmp_path):
    """Energy properties are reported in kJ mol-1 and multipoles in atomic units, as
    everywhere else in the analysis code."""

    energy_model = make_model(tmp_path, property_name="iqa")
    multipole_model = make_model(tmp_path, property_name="q00")

    report = overfitting_report(
        [energy_model, multipole_model], csv_files_list=None, output_location=None
    )

    units = dict(zip(report["property"], report["units"]))
    assert units["iqa"] == "kJ mol-1"
    assert units["q00"] == "atomic units"

    for column in ("ntrain", "train_rmse", "loo_rmse", "weights_mismatch", "diagnosis"):
        assert column in report.columns


def write_ferebus_csv(directory, atom: str, property_name: str, x, y):
    """Writes a held-out split in the FEREBUS/ichor CSV layout: feature columns
    ``f1..fN`` plus one column named after the property, in a file named
    ``<system>_<atom>_<SPLIT>.csv``."""

    import pandas as pd

    frame = pd.DataFrame(x, columns=[f"f{i + 1}" for i in range(x.shape[1])])
    frame[property_name] = y

    path = directory / f"SYS_{atom}_EXT_VALIDATION_SET.csv"
    frame.to_csv(path, index=False)

    return path


def test_report_reads_held_out_ferebus_csvs(tmp_path):
    """The report finds each model's held-out CSV by the FEREBUS file-naming
    convention and writes a report covering every model."""

    model = make_model(tmp_path, property_name="q00")

    rng = np.random.default_rng(21)
    x_test = rng.uniform(0.0, 1.0, (40, N_FEATURES))
    csv_path = write_ferebus_csv(tmp_path, "O1", "q00", x_test, smooth_function(x_test))

    output = tmp_path / "report.csv"
    report = overfitting_report(
        [model],
        csv_files_list=[csv_path],
        split_name="EXT_VALIDATION_SET",
        output_location=output,
    )

    assert len(report) == 1
    row = report.iloc[0]
    assert row["split"] == "EXT_VALIDATION_SET"
    assert row["heldout_n"] == 40
    assert np.isfinite(row["overfit_ratio"])
    assert row["diagnosis"] == DIAGNOSIS_OK
    assert output.is_file()


def test_report_skips_models_with_no_matching_csv(tmp_path):
    """A model with no held-out CSV still gets its leave-one-out columns rather than
    being dropped from the report."""

    matched = make_model(tmp_path, property_name="q00")
    unmatched = make_model(tmp_path, property_name="q10", seed=4)

    rng = np.random.default_rng(22)
    x_test = rng.uniform(0.0, 1.0, (30, N_FEATURES))
    csv_path = write_ferebus_csv(tmp_path, "O1", "q00", x_test, smooth_function(x_test))

    report = overfitting_report(
        [matched, unmatched], csv_files_list=[csv_path], output_location=None
    )

    by_property = report.set_index("property")
    assert by_property.loc["q00", "heldout_n"] == 30
    assert by_property.loc["q10", "heldout_n"] == 0
    assert np.isfinite(by_property.loc["q10", "loo_rmse"])
