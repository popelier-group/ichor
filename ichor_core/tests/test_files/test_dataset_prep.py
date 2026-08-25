"""Tests for the dataset preparation script which is written out for polus to run.

The script splits the geometries which come through the outlier and q00 filters into a
training, a validation and a test set. How many geometries survive those filters is only
known on the compute node, so the script works it out for itself and scales the three
sizes down when they no longer fit, which is what is tested here: the script is written
out, its helpers are taken out of it, and they are run against the sizes and counts they
are there for.
"""

import ast
from pathlib import Path

import pytest
from ichor.core.files.polus.dataset_prep import DatasetPrepScript


def written_script(tmp_path, **kwargs) -> str:
    """Writes the dataset preparation script and returns its text."""

    script = DatasetPrepScript(
        tmp_path / "dataset_split.py", outlier_input_dir="processed_csvs", **kwargs
    )
    script.write()

    return script.path.read_text()


def script_functions(script_text: str) -> dict:
    """Returns the functions the script defines, so that what the job runs is what is
    tested rather than a copy of it.

    The script imports polus, which is not installed here (and would run a whole
    calculation if it were), so the function definitions are taken out of it and run on
    their own.
    """

    module = ast.parse(script_text)
    functions = ast.Module(
        body=[
            node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.Import))
        ],
        type_ignores=[],
    )

    namespace = {}
    exec(compile(functions, "<dataset_split.py>", "exec"), namespace)  # noqa: S102

    return namespace


@pytest.fixture
def functions(tmp_path):
    """The helpers of a freshly written dataset preparation script."""
    return script_functions(written_script(tmp_path))


def test_the_written_script_is_valid_python(tmp_path):

    script_text = written_script(
        tmp_path, train_size=[500, 1000], val_size=200, test_size=200
    )

    # the script is written from a template, so a mistake in it is only found when the
    # job runs unless it is compiled here
    compile(script_text, "<dataset_split.py>", "exec")

    assert "TRAIN = [500, 1000]" in script_text
    assert "VALID = 200" in script_text
    assert "TEST = 200" in script_text


def test_the_sizes_of_the_sets_are_written_as_single_numbers(tmp_path):
    """The validation and test sets are one size each, whether they are given as a
    number or as the list of one which the sampler itself takes."""

    script_text = written_script(tmp_path, val_size=[200], test_size=[300])

    assert "VALID = 200" in script_text
    assert "TEST = 300" in script_text

    # and the defaults are numbers as well, not the lists they used to be
    script_text = written_script(tmp_path)
    assert "VALID = 250" in script_text
    assert "TEST = 1000" in script_text


def test_sizes_which_fit_are_left_alone(functions):

    sizes_which_fit = functions["sizes_which_fit"]

    assert sizes_which_fit(500, 200, 200, 1000) == (500, 200, 200)
    # exactly filling what there is is still fitting
    assert sizes_which_fit(500, 200, 300, 1000) == (500, 200, 300)


def test_sizes_which_do_not_fit_are_scaled_in_proportion(functions):
    """The example of the menu: 900 geometries are asked for and only 850 come through
    the filters, so all three sets come down by the same share rather than the shortfall
    being taken out of one of them."""

    sizes_which_fit = functions["sizes_which_fit"]

    train, valid, test = sizes_which_fit(500, 200, 200, 850)

    assert train + valid + test <= 850
    # nothing was given away that did not have to be
    assert train + valid + test >= 848
    # a 50/20/20 split stays a 50/20/20 split
    assert train == pytest.approx(850 * 500 / 900, abs=2)
    assert valid == pytest.approx(850 * 200 / 900, abs=2)
    assert test == pytest.approx(850 * 200 / 900, abs=2)


def test_scaling_never_empties_a_set(functions):
    """A set of no geometries is of no use to anything downstream, so every set keeps at
    least one geometry however little is left."""

    sizes_which_fit = functions["sizes_which_fit"]

    for available in range(3, 20):
        train, valid, test = sizes_which_fit(10_000, 5_000, 5_000, available)
        assert min(train, valid, test) >= 1
        assert train + valid + test <= available


def test_too_few_geometries_to_split_is_an_error(functions):
    """Two geometries cannot be a training, a validation and a test set, and saying so is
    better than writing out sets which are empty."""

    sizes_which_fit = functions["sizes_which_fit"]

    with pytest.raises(ValueError, match="not enough"):
        sizes_which_fit(500, 200, 200, 2)


def test_geometries_are_counted_from_the_filtered_csv_files(functions, tmp_path):

    geometries_in = functions["geometries_in"]

    filtered = tmp_path / "FILTERED-BY-Q00"
    filtered.mkdir()
    for atom in ("o1", "h2", "h3"):
        (filtered / f"{atom}_iqa.csv").write_text(
            "f1,f2,f3,iqa\n" + "".join(f"1.0,2.0,3.0,{i}\n" for i in range(42))
        )

    # every atom holds the same geometries, so one file is the count
    assert geometries_in(str(filtered)) == 42


def test_counting_an_empty_directory_gives_no_geometries(functions, tmp_path):

    geometries_in = functions["geometries_in"]

    empty = tmp_path / "FILTERED-BY-Q00"
    empty.mkdir()

    assert geometries_in(str(empty)) == 0


class FakeSeqSampler:
    """Stands in for the polus sampler, recording the sizes it was asked for and making
    the directory it would have made.

    polus names that directory ``SEQ-<train>-<valid>-<test>`` after the sizes it is
    given (see ``SeqSampler.generateFerebusInputs``), which is the one line of its
    behaviour reproduced here, as it is what tells the user which sizes the sets in it
    actually are.
    """

    calls = []

    def __init__(self, **kwargs):
        FakeSeqSampler.calls.append(kwargs)
        self.inputDir = kwargs.get("inputDir")
        self.outputDir = kwargs.get("outputDir")
        self.trainSize = kwargs.get("trainSize")
        self.validSize = kwargs.get("validSize")
        self.testSize = kwargs.get("testSize")

    def Execute(self):
        train = self.trainSize
        name = f"SEQ-{train}-{self.validSize[0]}-{self.testSize[0]}"
        (Path(self.outputDir) / name).mkdir(parents=True, exist_ok=True)


def run_script(script_text: str, tmp_path, monkeypatch, ngeometries: int) -> list:
    """Runs a written dataset preparation script against a set of filtered csv files,
    with polus stood in for, and returns the sizes the sampler was asked for.

    This runs the script the job would run rather than a copy of its parts, so the
    scaling is tested where it actually happens.
    """

    import sys
    import types

    def fake_module(name, **contents):
        module = types.ModuleType(name)
        for attribute, value in contents.items():
            setattr(module, attribute, value)
        monkeypatch.setitem(sys.modules, name, module)
        return module

    class DoesNothing:
        def __init__(self, **kwargs):
            pass

        def Execute(self):
            pass

        def write_raw_and_corrected_atomic_iqa_energies(self):
            pass

        def write_corrected_reference_data(self):
            pass

    fake_module("polus")
    fake_module("polus.samplers")
    fake_module("polus.samplers.SEQ")
    fake_module("polus.samplers.SEQ.Seq", SeqSampler=FakeSeqSampler)
    fake_module("polus.filters")
    fake_module(
        "polus.filters.RecoveryManager",
        IqaFilter=DoesNothing,
        Q00Filter=DoesNothing,
        DualFilter=DoesNothing,
    )
    fake_module("polus.filters.outliers", Odd=DoesNothing)
    fake_module("polus.filters.iqa_correction", iqa_correct=DoesNothing)

    # what the q00 filter would have left behind for the sampler
    filtered = tmp_path / "filtered" / "FILTERED-BY-Q00"
    filtered.mkdir(parents=True)
    (filtered / "o1_iqa.csv").write_text(
        "f1,iqa\n" + "".join(f"1.0,{i}\n" for i in range(ngeometries))
    )

    monkeypatch.chdir(tmp_path)
    FakeSeqSampler.calls = []
    exec(compile(script_text, "<dataset_split.py>", "exec"), {"__name__": "__main__"})

    return [
        (call["trainSize"], call["validSize"][0], call["testSize"][0])
        for call in FakeSeqSampler.calls
    ]


def test_the_script_splits_at_the_sizes_it_was_given_when_they_fit(
    tmp_path, monkeypatch
):

    script_text = written_script(
        tmp_path, train_size=[500, 1000], val_size=200, test_size=200
    )

    splits = run_script(script_text, tmp_path, monkeypatch, ngeometries=2000)

    assert splits == [(500, 200, 200), (1000, 200, 200)]


def test_the_script_scales_the_sizes_down_when_the_filters_leave_too_few(
    tmp_path, monkeypatch
):
    """900 geometries are asked for and 850 come through the filters, so the split is
    scaled to fit rather than the test set quietly coming back short."""

    script_text = written_script(
        tmp_path, train_size=[500], val_size=200, test_size=200
    )

    splits = run_script(script_text, tmp_path, monkeypatch, ngeometries=850)

    (train, valid, test) = splits[0]
    assert train + valid + test <= 850
    assert (train, valid, test) != (500, 200, 200)
    # the shares the sizes were asked for are kept
    assert train == pytest.approx(850 * 500 / 900, abs=2)
    assert valid == test == pytest.approx(850 * 200 / 900, abs=2)


def dataset_directories(tmp_path) -> list:
    """The dataset directories which were written, as <train folder>/<seq folder>."""

    return sorted(
        f"{seq.parent.name}/{seq.name}"
        for seq in (tmp_path / "DATASETS").glob("*/SEQ-*")
    )


def test_the_dataset_directories_are_named_after_the_sizes_which_were_used(
    tmp_path, monkeypatch
):
    """The sizes the sets end up being are the ones in the names of the directories they
    are written into, so a split which was scaled down says so where it is looked at."""

    script_text = written_script(
        tmp_path, train_size=[500], val_size=250, test_size=250
    )

    # every geometry comes through the filters, so nothing is scaled
    run_script(script_text, tmp_path, monkeypatch, ngeometries=1000)
    assert dataset_directories(tmp_path) == ["TRAIN-500/SEQ-500-250-250"]


def test_a_scaled_split_is_named_after_the_sizes_it_was_scaled_to(
    tmp_path, monkeypatch
):
    """500/250/250 needs 1000 geometries; when only 800 come through the filters the
    split becomes 400/200/200, and it is that which names the directories rather than
    the sizes which were asked for."""

    script_text = written_script(
        tmp_path, train_size=[500], val_size=250, test_size=250
    )

    splits = run_script(script_text, tmp_path, monkeypatch, ngeometries=800)

    assert splits == [(400, 200, 200)]
    assert dataset_directories(tmp_path) == ["TRAIN-400/SEQ-400-200-200"]


def test_the_script_scales_each_training_set_size_on_its_own(tmp_path, monkeypatch):
    """A learning curve asks for several training set sizes; the ones which fit are left
    alone and only the ones which do not are scaled."""

    script_text = written_script(
        tmp_path, train_size=[100, 5000], val_size=100, test_size=100
    )

    splits = run_script(script_text, tmp_path, monkeypatch, ngeometries=1000)

    assert splits[0] == (100, 100, 100)
    scaled_train, scaled_valid, scaled_test = splits[1]
    assert scaled_train + scaled_valid + scaled_test <= 1000
    assert scaled_train < 5000
