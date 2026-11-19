"""Tests for changing the hpc block of the config from inside ichor.

The config is the user's file, often annotated, so the edits have to change only what
they were asked to and leave the rest of the file as it was written.
"""

from importlib.resources import files

import ichor.hpc.global_variables
import pytest
import yaml

from ichor.hpc import hpc_settings
from ichor.hpc.hpc_settings import HpcSettingsError

TEMPLATE = files("ichor.hpc") / "data" / "config_template.yaml"


@pytest.fixture
def config(tmp_path):
    """A copy of the example config, which has comments and both forms of memory."""

    path = tmp_path / "config.yaml"
    path.write_text(TEMPLATE.read_text())
    return path


def read_hpc(path, machine="csf3"):
    with open(path) as f:
        return yaml.safe_load(f)[machine]["hpc"]


@pytest.mark.parametrize(
    "walltime", ["3-0", "1-12:00:00", "24:00:00", "90", "90:00", "2-6", " 3-0 "]
)
def test_walltimes_slurm_accepts_are_kept(walltime):
    assert hpc_settings.normalise_walltime(walltime) == walltime.strip()


@pytest.mark.parametrize("walltime", ["3 days", "3d", "-1", "1:2:3:4", "", "1-"])
def test_walltimes_slurm_rejects_are_refused(walltime):
    with pytest.raises(HpcSettingsError):
        hpc_settings.normalise_walltime(walltime)


def test_no_walltime_is_accepted_in_any_case():
    assert hpc_settings.normalise_walltime("None") == "none"


@pytest.mark.parametrize(
    "existing, taken, remaining",
    [
        ((2, 168), (2, 32), [(33, 168)]),
        ((2, 168), (100, 200), [(2, 99)]),
        ((2, 32), (1, 64), []),
        ((2, 168), (10, 20), [(2, 9), (21, 168)]),
    ],
)
def test_remaining_range(existing, taken, remaining):
    assert hpc_settings.remaining_range(existing, taken) == remaining


def test_overlaps_and_gaps_are_reported():
    problems = hpc_settings.range_problems(
        {"serial": (1, 1), "multicore": (4, 168), "multicore_small": (4, 32)}
    )

    assert any("both cover 4-32 cores" in p for p in problems)
    assert any("No partition covers 2-3 cores" in p for p in problems)


def test_ranges_that_fit_together_have_no_problems():
    assert not hpc_settings.range_problems(
        {"serial": (1, 1), "multicore_small": (2, 32), "multicore": (33, 168)}
    )


def test_moving_small_jobs_to_another_partition(config):
    """The case this exists for: sending 2-32 core jobs to multicore_small rather
    than multicore, which keeps 33 and up."""

    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.trim_partition(hpc, "multicore", (2, 32))
        hpc_settings.set_partition(hpc, "multicore_small", 2, 32)
        hpc_settings.set_partition_memory_per_core_gb(hpc, "multicore_small", 4)

    hpc = read_hpc(config)
    assert hpc["parallel_environments"] == {
        "serial": [1, 1],
        "multicore": [33, 168],
        "multicore_small": [2, 32],
    }
    assert hpc["memory_per_core_gb"]["multicore_small"] == 4

    text = config.read_text()
    # written on one line, as the rest of the file has them
    assert "multicore_small: [2, 32]" in text


def test_edits_leave_the_rest_of_the_file_alone(config):
    before = config.read_text()

    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.set_max_walltime(hpc, "1-0")

    after = config.read_text()
    changed = [
        (old, new)
        for old, new in zip(before.splitlines(), after.splitlines())
        if old != new
    ]

    assert len(before.splitlines()) == len(after.splitlines())
    # only csf3's time limit changed, and it kept its quotes
    assert changed == [('    max_walltime: "3-0"', '    max_walltime: "1-0"')]


def test_the_previous_config_is_kept(config):
    before = config.read_text()

    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.set_max_walltime(hpc, "1-0")

    assert hpc_settings.backup_path(config).read_text() == before


def test_a_failed_change_leaves_the_file_untouched(config):
    before = config.read_text()

    with pytest.raises(HpcSettingsError):
        with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
            hpc_settings.set_max_walltime(hpc, "1-0")
            hpc_settings.rename_partition(hpc, "does_not_exist", "other")

    assert config.read_text() == before
    assert not hpc_settings.backup_path(config).exists()


def test_renaming_a_partition_renames_its_memory_and_keeps_its_place(config):
    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.rename_partition(hpc, "serial", "short")

    hpc = read_hpc(config)
    assert list(hpc["parallel_environments"]) == ["short", "multicore"]
    assert list(hpc["memory_per_core_gb"]) == ["short", "multicore"]
    assert hpc["memory_per_core_gb"]["short"] == 5


def test_renaming_onto_an_existing_partition_is_refused(config):
    with pytest.raises(HpcSettingsError, match="already"):
        with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
            hpc_settings.rename_partition(hpc, "serial", "multicore")


def test_removing_a_partition_removes_its_memory(config):
    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.remove_partition(hpc, "serial")

    hpc = read_hpc(config)
    assert "serial" not in hpc["parallel_environments"]
    assert "serial" not in hpc["memory_per_core_gb"]


def test_a_partition_cannot_be_split_in_two(config):
    with pytest.raises(HpcSettingsError, match="split"):
        with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
            hpc_settings.trim_partition(hpc, "multicore", (10, 20))


def test_memory_can_switch_between_one_number_and_per_partition(config):
    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.set_memory_per_core_gb(hpc, 6.0)
    assert read_hpc(config)["memory_per_core_gb"] == 6

    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.set_memory_per_core_gb(hpc, {"serial": 5, "multicore": 7.5})
    assert read_hpc(config)["memory_per_core_gb"] == {"serial": 5, "multicore": 7.5}


def test_an_hpc_block_is_made_for_a_machine_without_one(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("mymachine:\n  software: {}\n")

    with hpc_settings.edit_hpc_block(path, "mymachine") as hpc:
        hpc_settings.set_partition(hpc, "compute", 1, 64)

    assert read_hpc(path, "mymachine") == {
        "parallel_environments": {"compute": [1, 64]}
    }


def test_a_machine_not_in_the_config_is_refused(config):
    with pytest.raises(HpcSettingsError, match="no block"):
        with hpc_settings.edit_hpc_block(config, "elsewhere"):
            pass


def test_reloading_picks_up_new_partitions(config, monkeypatch):
    """Partitions are built once when ichor starts, so a change only reaches the next
    job if they are built again."""

    monkeypatch.setattr(ichor.hpc.global_variables, "ICHOR_CONFIG_PATH", config)
    monkeypatch.setattr(ichor.hpc.global_variables, "MACHINE", "csf3")
    # put back whatever was there before once the test is over
    monkeypatch.setattr(ichor.hpc.global_variables, "ICHOR_CONFIG", {})
    monkeypatch.setattr(
        ichor.hpc.global_variables,
        "PARALLEL_ENVIRONMENT",
        ichor.hpc.global_variables.ParallelEnvironment(),
    )

    with hpc_settings.edit_hpc_block(config, "csf3") as hpc:
        hpc_settings.trim_partition(hpc, "multicore", (2, 32))
        hpc_settings.set_partition(hpc, "multicore_small", 2, 32)

    ichor.hpc.global_variables.reload_config()

    environment = ichor.hpc.global_variables.PARALLEL_ENVIRONMENT
    assert environment[16] == "multicore_small"
    assert environment[64] == "multicore"
