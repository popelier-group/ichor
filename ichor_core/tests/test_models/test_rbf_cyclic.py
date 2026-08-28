"""Tests for the cyclic feature correction of :class:`RBFCyclic`.

The correction exists to wrap the phi angles, whose period is 2 pi. Which columns of
a kernel are phi angles depends on the kernel's active dimensions, not on their
position in the block the kernel selects: FEREBUS writes models whose features are
split across an ``rbf-cyclic`` over the distances and theta angles and a ``periodic``
over the phi angles, and the first of those must not wrap anything at all.
"""

import numpy as np
import pytest
from ichor.core.analysis.overfitting import (
    leave_one_out_predictions,
    WEIGHTS_MISMATCH_THRESHOLD,
)
from ichor.core.models import Model
from ichor.core.models.kernels import RBFCyclic
from tests.path import get_cwd

# the real FEREBUS models the wrapping bug was found on
MODEL_CHECK_DIR = (
    get_cwd(__file__) / ".." / ".." / ".." / "example_files" / "model_check"
)

H12_MODELS = [
    "BZAMID_MOL_OPTIMISED-SAMPLE-1000_iqa_H12.model",
    "BZAMID_MOL_OPTIMISED-SAMPLE-1000_q00_H12.model",
    "BZAMID_MOL_OPTIMISED-SAMPLE-1000_q10_H12.model",
    "BZAMID_MOL_OPTIMISED-SAMPLE-1000_q11c_H12.model",
    "BZAMID_MOL_OPTIMISED-SAMPLE-1000_q11s_H12.model",
]

# an atom of a 5 atom system has 9 features: r, r, theta, then (r, theta, phi) twice,
# so features 5 and 8 are the phi angles and the other seven are not
N_FEATURES = 9
PHI_FEATURES = [5, 8]
NON_PHI_FEATURES = [0, 1, 2, 3, 4, 6, 7]


def test_mask_selects_the_phi_features_of_a_full_feature_set():
    """A kernel over every feature wraps exactly the phi angles - and nothing else,
    in particular not feature 2, which is a theta angle."""

    kernel = RBFCyclic("k1", np.ones(N_FEATURES))

    assert list(kernel.active_dims[kernel.mask]) == PHI_FEATURES


def test_mask_is_empty_when_the_kernel_holds_no_phi_features():
    """The ``rbf-cyclic`` half of a FEREBUS model whose phi angles are handled by a
    separate periodic kernel has nothing to wrap."""

    kernel = RBFCyclic(
        "k1",
        np.ones(len(NON_PHI_FEATURES)),
        active_dims=np.array(NON_PHI_FEATURES),
    )

    assert kernel.mask.size == 0


def test_mask_follows_the_phi_features_through_the_active_dimensions():
    """The correction applies to the phi angles wherever they land in the block the
    kernel selects, which is not every third column of it."""

    active_dims = np.array([2, 4, 5, 7, 8])
    kernel = RBFCyclic("k1", np.ones(len(active_dims)), active_dims=active_dims)

    # the phi angles 5 and 8 sit at positions 2 and 4 of this block
    assert list(kernel.mask) == [2, 4]
    assert list(active_dims[kernel.mask]) == PHI_FEATURES


def test_no_wrapping_of_a_distance_feature_with_a_range_wider_than_pi():
    """A kernel holding no phi angles is a plain RBF, even when two of its points are
    more than 2 pi apart in one feature.

    This is what the bug came down to: wrapping such a feature turns a large
    separation into a small one and so invents a high covariance between two points
    that are nowhere near each other.
    """

    thetas = np.linspace(0.1, 0.9, len(NON_PHI_FEATURES))
    kernel = RBFCyclic("k1", thetas, active_dims=np.array(NON_PHI_FEATURES))

    x1 = np.zeros((1, N_FEATURES))
    x2 = np.zeros((1, N_FEATURES))
    # feature 6 is a distance, and is the column the correction used to be applied to
    x2[0, 6] = 3.0 * np.pi

    difference = (x2 - x1)[:, NON_PHI_FEATURES]
    expected = np.exp(-np.sum(thetas * difference**2))

    assert kernel.k(x1, x2).item() == pytest.approx(expected)
    # and the two points are correctly seen as all but uncorrelated
    assert kernel.k(x1, x2).item() < 1e-6


@pytest.mark.parametrize("model_name", H12_MODELS)
def test_ferebus_models_are_internally_consistent(model_name):
    """Regression test: the weights FEREBUS stored in these files are ``R^-1 (y - m)``
    for the covariance matrix ichor rebuilds from their hyperparameters.

    H12 of this system is the case the wrapping bug was found on. Its features put a
    distance spanning more than pi into a column the correction used to be applied to,
    which left every one of its models reported as ``inconsistent`` by the overfitting
    check even though the files were written correctly.
    """

    model_path = MODEL_CHECK_DIR / model_name
    if not model_path.exists():
        pytest.skip(f"{model_name} is not available")

    mismatch = leave_one_out_predictions(Model(model_path)).weights_mismatch

    assert mismatch < WEIGHTS_MISMATCH_THRESHOLD
