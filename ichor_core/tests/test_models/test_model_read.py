"""Tests that a malformed model file is rejected when it is read.

The training inputs, the training labels and the weights are read into arrays sized
from the ``number_of_training_points`` of the header, so a block which does not hold
that many rows has to be caught at read time: the tail of the array is uninitialised
memory, and a model built on it predicts perfectly happily from values that were never
in the file.
"""

from pathlib import Path

import numpy as np
import pytest
from ichor.core.files.file import FileReadError
from ichor.core.models import Model
from tests.path import get_cwd

MODEL_CHECK_DIR = (
    get_cwd(__file__) / ".." / ".." / ".." / "example_files" / "model_check"
)
GOOD_MODEL = MODEL_CHECK_DIR / "BZAMID_MOL_OPTIMISED-SAMPLE-1000_iqa_H12.model"

BLOCKS = ["training_data.x", "training_data.y", "weights"]


@pytest.fixture
def good_model_lines() -> list:
    if not GOOD_MODEL.exists():
        pytest.skip(f"{GOOD_MODEL.name} is not available")
    return GOOD_MODEL.read_text().splitlines()


def block_start(lines: list, block_name: str) -> int:
    """The index of the first data row of ``block_name``."""

    return lines.index(f"[{block_name}]") + 1


def write_model(tmp_path: Path, lines: list) -> Model:
    """Writes ``lines`` to a model file and reads it.

    ``Model`` reads lazily - the file is not touched until an attribute of it is asked
    for - so the read is forced here rather than left to whichever attribute a test
    happens to reach for first.
    """

    path = tmp_path / GOOD_MODEL.name
    path.write_text("\n".join(lines) + "\n")

    model = Model(path)
    model.read()

    return model


def test_a_well_formed_file_still_reads(good_model_lines, tmp_path):
    """The guard does not get in the way of a file that is not malformed."""

    model = write_model(tmp_path, good_model_lines)

    assert model.x.shape == (model.ntrain, model.nfeats)
    assert model.y.shape == (model.ntrain, 1)
    assert model.weights.shape == (model.ntrain, 1)
    assert np.isfinite(model.x).all()
    assert np.isfinite(model.y).all()
    assert np.isfinite(model.weights).all()


@pytest.mark.parametrize("block_name", BLOCKS)
def test_a_block_short_of_a_row_is_rejected(good_model_lines, tmp_path, block_name):
    """One missing row is enough: it is the tail of the array that would be left
    uninitialised, and nothing downstream would notice."""

    lines = list(good_model_lines)
    del lines[block_start(lines, block_name)]

    with pytest.raises(FileReadError, match=block_name):
        write_model(tmp_path, lines)


@pytest.mark.parametrize("block_name", BLOCKS)
def test_a_truncated_file_is_rejected(good_model_lines, tmp_path, block_name):
    """A file that stops part way through a block, as an interrupted write leaves it."""

    lines = good_model_lines[: block_start(good_model_lines, block_name) + 3]

    with pytest.raises(FileReadError, match=block_name):
        write_model(tmp_path, lines)


def test_a_row_with_too_few_values_is_rejected(good_model_lines, tmp_path):
    """A short row would otherwise fail to broadcast into the array, which says
    nothing about which file or which row is at fault."""

    lines = list(good_model_lines)
    row = block_start(lines, "training_data.x")
    lines[row] = " ".join(lines[row].split()[:-1])

    with pytest.raises(FileReadError, match="training_data.x"):
        write_model(tmp_path, lines)


def test_a_value_that_is_not_a_number_is_rejected(good_model_lines, tmp_path):
    """What a Fortran write overflow leaves behind."""

    lines = list(good_model_lines)
    row = block_start(lines, "training_data.y")
    lines[row] = "*" * 20

    with pytest.raises(FileReadError, match="training_data.y"):
        write_model(tmp_path, lines)
