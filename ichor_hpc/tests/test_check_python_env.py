"""Tests for the preflight check on the conda environment that the ASE optimisation
and metadynamics jobs run in.

The point of the check is that a job which cannot possibly work is refused on the
login node instead of failing on a compute node, so what matters here is that each
way of being misconfigured is detected and named.
"""

import sys

import ichor.hpc.global_variables

import pytest

from ichor.hpc.check_python_env import (
    check_configured_python_environment,
    configured_python_path,
    missing_modules,
    PythonEnvironmentNotConfigured,
    PythonEnvironmentPackagesMissing,
)

MACHINE = "test_machine"


@pytest.fixture
def config(monkeypatch):
    """Installs a config for a known machine and returns a function that sets the
    ``software.python`` block of it."""

    def set_python_block(**settings):
        monkeypatch.setattr(
            ichor.hpc.global_variables,
            "ICHOR_CONFIG",
            {MACHINE: {"software": {"python": dict(settings)}}},
        )
        monkeypatch.setattr(ichor.hpc.global_variables, "MACHINE", MACHINE)

    return set_python_block


def test_python_path_has_user_expanded(config):
    """The config is written with ~ in it, but the check has to look the interpreter
    up on disk, where ~ means nothing."""

    config(env_name="ichor_ase", python_path="~/.conda/envs/ichor_ase/bin/python")

    assert "~" not in str(configured_python_path())


def test_no_python_block_is_reported(config):
    """A config with no software.python block at all, which is how the example
    config used to ship for some machines."""

    config()

    with pytest.raises(PythonEnvironmentNotConfigured) as error:
        check_configured_python_environment(["ase"], "ASE optimisation jobs")

    # both missing keys are named, so it is clear what has to be added
    assert "software.python.env_name" in str(error.value)
    assert "software.python.python_path" in str(error.value)
    assert "are not set" in str(error.value)


def test_only_env_name_missing_is_reported_in_the_singular(config):
    """Only one key is missing, so the message should not read as if two are."""

    config(python_path=sys.executable)

    with pytest.raises(PythonEnvironmentNotConfigured) as error:
        check_configured_python_environment(["ase"], "ASE optimisation jobs")

    assert "software.python.env_name is not set" in str(error.value)


def test_interpreter_that_does_not_exist_is_reported(config, tmp_path):
    """A path that was configured but never created, which is what a half finished
    setup looks like."""

    config(env_name="ichor_ase", python_path=str(tmp_path / "nowhere" / "python"))

    with pytest.raises(PythonEnvironmentNotConfigured) as error:
        check_configured_python_environment(["ase"], "ASE optimisation jobs")

    assert "does not exist" in str(error.value)


def test_missing_packages_are_named_with_their_conda_package_names(config):
    """conda-forge does not name these packages after the modules they provide, so
    listing the failed imports would give an install command that does not work."""

    config(env_name="ichor_ase", python_path=sys.executable)

    with pytest.raises(PythonEnvironmentPackagesMissing) as error:
        check_configured_python_environment(
            ["definitely_not_a_real_module", "xtb", "plumed"],
            "metadynamics jobs",
        )

    message = str(error.value)
    assert "conda install -n ichor_ase -c conda-forge" in message
    assert "xtb-python" in message
    assert "py-plumed" in message


def test_environment_with_everything_passes(config):
    """The interpreter running the tests has these, so the check must not object."""

    config(env_name="ichor_ase", python_path=sys.executable)

    check_configured_python_environment(["sys", "json"], "ASE optimisation jobs")


def test_missing_modules_only_reports_what_is_absent():
    """Modules that are present must not be reported, or the install command would
    tell the user to reinstall things that are already there."""

    missing = missing_modules(sys.executable, ["json", "not_a_real_module_at_all"])

    assert missing == ["not_a_real_module_at_all"]


def test_unrunnable_interpreter_is_reported(config, tmp_path):
    """A path that exists but is not a working interpreter, such as a broken conda
    environment or a file that is not an executable at all."""

    not_an_interpreter = tmp_path / "python"
    not_an_interpreter.write_text("this is not an interpreter")
    config(env_name="ichor_ase", python_path=str(not_an_interpreter))

    with pytest.raises(PythonEnvironmentNotConfigured):
        check_configured_python_environment(["ase"], "ASE optimisation jobs")
