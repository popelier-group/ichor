"""Tests for the config that a SLURM cluster needs before ichor can submit to it.

Each of these covers a way a site which is not one of the Manchester clusters ends
up with a submission script the batch system rejects, which is only discovered when
sbatch refuses the job (or, worse, when the job is killed on the node).
"""

import ichor.hpc.global_variables
import pytest

from ichor.hpc.batch_system import NoPartitionForCoreCount, SLURM
from ichor.hpc.submission_commands import GaussianCommand
from ichor.hpc.submission_script.submission_script import max_walltime

MACHINE = "test_machine"


@pytest.fixture
def hpc_config(monkeypatch):
    """Installs an hpc block for a known machine and returns a function that sets
    the keys in it."""

    def set_hpc_block(**settings):
        monkeypatch.setattr(
            ichor.hpc.global_variables,
            "ICHOR_CONFIG",
            {MACHINE: {"hpc": dict(settings)}},
        )
        monkeypatch.setattr(ichor.hpc.global_variables, "MACHINE", MACHINE)

    return set_hpc_block


@pytest.fixture
def partitions(monkeypatch):
    """Sets the partitions that are configured for the current machine."""

    def set_partitions(**ranges):
        environment = ichor.hpc.global_variables.ParallelEnvironment()
        for name, bounds in ranges.items():
            environment[name] = bounds
        monkeypatch.setattr(
            ichor.hpc.global_variables, "PARALLEL_ENVIRONMENT", environment
        )

    return set_partitions


def test_walltime_defaults_when_the_key_is_absent(hpc_config):
    """An existing config which predates the key keeps the behaviour it had."""

    hpc_config()

    assert max_walltime() == ichor.hpc.global_variables.DEFAULT_MAX_WALLTIME


def test_walltime_is_read_from_the_config(hpc_config):
    """A cluster whose partitions allow less than the default has to be able to say
    so, or SLURM rejects every job it submits."""

    hpc_config(max_walltime="24:00:00")

    assert max_walltime() == "24:00:00"


def test_walltime_can_be_turned_off(hpc_config):
    """Writing no time limit lets the partition apply its own default, which is what
    a site that does not want ichor choosing one needs."""

    hpc_config(max_walltime="none")

    assert max_walltime() is None


def test_walltime_off_is_case_insensitive(hpc_config):
    """The value is written by hand into a YAML file, so the capitalisation of it
    should not decide whether jobs get a seven day limit."""

    hpc_config(max_walltime="None")

    assert max_walltime() is None


def test_gaussian_memory_falls_back_rather_than_failing(hpc_config):
    """A config with no memory_per_core_gb used to reach the arithmetic as None and
    raise a TypeError, which said nothing about which setting was missing."""

    hpc_config()

    with pytest.warns(UserWarning, match="memory_per_core_gb"):
        assert (
            GaussianCommand.memory_per_core
            == ichor.hpc.global_variables.DEFAULT_MEMORY_PER_CORE_GB
        )


def test_gaussian_memory_is_read_from_the_config(hpc_config):
    """The configured value is used, and does not warn."""

    hpc_config(memory_per_core_gb=16)

    assert GaussianCommand.memory_per_core == 16


def test_core_count_below_every_partition_is_an_error(hpc_config, partitions):
    """A one core job used to be written out as a bare `-p`, which sbatch rejects
    without saying which setting was missing."""

    hpc_config()
    partitions(compute=(2, 64))

    with pytest.raises(NoPartitionForCoreCount) as error:
        SLURM.parallel_environment(1)

    message = str(error.value)
    assert "1 core " in message, "the count should not be pluralised"
    assert "compute: [2, 64]" in message, "what is configured should be shown"
    assert "hpc.parallel_environments" in message


def test_core_count_above_every_partition_is_an_error(hpc_config, partitions):
    """Asking for more cores than any partition covers."""

    hpc_config()
    partitions(compute=(2, 64))

    with pytest.raises(NoPartitionForCoreCount) as error:
        SLURM.parallel_environment(128)

    assert "128 cores" in str(error.value)


def test_no_partitions_configured_at_all_is_an_error(hpc_config, partitions):
    """A machine whose hpc block has no parallel_environments."""

    hpc_config()
    partitions()

    with pytest.raises(NoPartitionForCoreCount) as error:
        SLURM.parallel_environment(8)

    assert "No partitions are configured" in str(error.value)


def test_a_covered_core_count_names_the_partition(hpc_config, partitions):
    """The ordinary case still works: the partition whose range covers the core
    count is written as -p, with the cores asked for as one task."""

    hpc_config()
    partitions(serial=(1, 1), compute=(2, 64))

    directives = SLURM.parallel_environment(8)

    assert "-p compute" in directives
    assert "--cpus-per-task=8" in directives
    assert "--nodes=1" in directives
