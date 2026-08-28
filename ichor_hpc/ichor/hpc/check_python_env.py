"""Preflight checks for the Python environment that submitted ASE jobs activate.

The ASE optimisation and metadynamics scripts ichor generates import ``ase`` and
``xtb`` (and, for metadynamics, ``plumed``). They import nothing from ichor, so
they do not have to run in ichor's own environment: they run in the conda
environment named by ``software.python`` in the ichor config file, which the
submission script activates.

That environment is the only place ``xtb`` has to exist. Installing it with pip
is not an option on Python 3.12 and newer, because the PyPI wheels stop at 3.11,
whereas conda-forge builds it for current interpreters. Keeping it out of ichor's
own dependencies is what lets ichor itself run on any supported Python.

The cost of that split is that a misconfigured environment is only discovered
once a job reaches a compute node and dies with a ``ModuleNotFoundError`` in an
error file nobody is watching. These checks run on the login node before anything
is submitted, and turn it into an immediate, actionable error instead.
"""

import subprocess

from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.hpc.global_variables import get_param_from_config

# how long to wait for the configured interpreter to answer before giving up.
# locating a handful of modules should be near instant, so a hang means something
# is wrong with the environment rather than that it is slow
IMPORT_CHECK_TIMEOUT_SECONDS = 60

# the modules the generated scripts import, by job type
ASE_OPTIMISATION_MODULES = ["ase", "xtb"]
METADYNAMICS_MODULES = ["ase", "xtb", "plumed", "numpy"]

# conda-forge does not always name a package after the module it provides, so the
# suggested install command has to be translated from what failed to import
CONDA_PACKAGE_NAMES = {
    "xtb": "xtb-python",
    "plumed": "py-plumed",
}

# run in the configured interpreter to find out what is missing. find_spec locates
# the modules without importing them, which is quicker and avoids any import side
# effects in the environment being checked
FIND_MISSING_MODULES = (
    "import importlib.util, sys;"
    'print(" ".join(m for m in sys.argv[1:] '
    "if importlib.util.find_spec(m) is None))"
)


class ConfiguredPythonEnvironmentError(Exception):
    """Base class for problems with the configured Python environment. Callers that
    only need to report that a job cannot be submitted can catch this."""


class PythonEnvironmentNotConfigured(ConfiguredPythonEnvironmentError):
    """The config file does not say which Python environment to use, or names one
    that is not there."""


class PythonEnvironmentPackagesMissing(ConfiguredPythonEnvironmentError):
    """The configured Python environment exists but does not have the packages that
    the submitted scripts import."""


def configured_python_setting(key: str) -> Optional[str]:
    """Reads one value out of the ``software.python`` block of the config file, for
    the machine ichor is running on.

    :param key: The name of the setting, such as ``env_name`` or ``python_path``.
    :return: The configured value, or None if it is not set.
    """

    return get_param_from_config(
        ichor.hpc.global_variables.ICHOR_CONFIG,
        ichor.hpc.global_variables.MACHINE,
        "software",
        "python",
        key,
    )


def configured_python_path() -> Optional[Path]:
    """Returns the interpreter that the submitted jobs run, with ``~`` expanded.

    :return: The path of the configured interpreter, or None if it is not set.
    """

    python_path = configured_python_setting("python_path")

    if python_path:
        return Path(python_path).expanduser()


def how_to_configure() -> str:
    """Returns the block of config that has to be filled in, ready to be pasted.

    :return: A description of what to add to the config file.
    """

    machine = ichor.hpc.global_variables.MACHINE or "<the name of this machine>"

    return (
        f"Add the following to {ichor.hpc.global_variables.CONFIG_DESCRIPTION}, "
        "filling in the paths for this cluster:\n"
        f"    {machine}:\n"
        "      software:\n"
        "        python:\n"
        "          env_name: ichor_ase\n"
        "          python_path: ~/.conda/envs/ichor_ase/bin/python\n"
        "          modules: [<the anaconda module for this cluster>]\n"
        "The environment.yml in the ichor repository creates an environment with "
        "everything these jobs need:\n"
        "    conda env create -f environment.yml"
    )


def missing_modules(python_path: Path, required_modules: List[str]) -> List[str]:
    """Asks the configured interpreter which of ``required_modules`` it cannot find.

    :param python_path: The interpreter to ask.
    :param required_modules: The top level module names to look for.
    :raises PythonEnvironmentNotConfigured: If the interpreter could not be run.
    :return: The modules that are not importable, in the order they were given.
    """

    try:
        result = subprocess.run(
            [str(python_path), "-c", FIND_MISSING_MODULES, *required_modules],
            capture_output=True,
            text=True,
            timeout=IMPORT_CHECK_TIMEOUT_SECONDS,
        )
    except OSError as error:
        raise PythonEnvironmentNotConfigured(
            f"The configured Python interpreter {python_path} could not be run "
            f"({error}). {how_to_configure()}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise PythonEnvironmentNotConfigured(
            f"The configured Python interpreter {python_path} did not respond within "
            f"{IMPORT_CHECK_TIMEOUT_SECONDS} seconds, so the environment could not "
            "be checked."
        ) from error

    if result.returncode != 0:
        raise PythonEnvironmentNotConfigured(
            f"The configured Python interpreter {python_path} exited with "
            f"{result.returncode} when asked which packages it has:\n"
            f"{result.stderr.strip()}"
        )

    return result.stdout.split()


def check_configured_python_environment(
    required_modules: List[str], job_description: str
) -> None:
    """Checks that the jobs about to be submitted will find the packages they import
    in the Python environment that the submission script activates.

    :param required_modules: The top level module names the generated scripts import.
    :param job_description: What is about to be submitted, used in the error message.
    :raises PythonEnvironmentNotConfigured: If the config does not name a Python
        environment, or names an interpreter that is not there.
    :raises PythonEnvironmentPackagesMissing: If the environment is missing any of
        ``required_modules``.
    """

    environment_name = configured_python_setting("env_name")
    python_path = configured_python_path()

    if not environment_name or not python_path:
        unset = [
            key
            for key, value in (
                ("env_name", environment_name),
                ("python_path", python_path),
            )
            if not value
        ]
        missing_keys = " and ".join(f"software.python.{key}" for key in unset)
        is_or_are = "is" if len(unset) == 1 else "are"
        raise PythonEnvironmentNotConfigured(
            f"The {job_description} run in a conda environment which has to be named "
            f"in the ichor config file, and {missing_keys} {is_or_are} not set for "
            f"this machine. {how_to_configure()}"
        )

    if not python_path.exists():
        raise PythonEnvironmentNotConfigured(
            f"The configured Python interpreter {python_path} does not exist, so every "
            f"one of the {job_description} would fail. {how_to_configure()}"
        )

    missing = missing_modules(python_path, required_modules)

    if missing:
        packages = " ".join(CONDA_PACKAGE_NAMES.get(name, name) for name in missing)
        raise PythonEnvironmentPackagesMissing(
            f"The conda environment {environment_name} ({python_path}) does not have "
            f"{', '.join(missing)}, which the {job_description} import, so every one "
            "of them would fail with a ModuleNotFoundError on the compute node. "
            "Install into that environment with:\n"
            f"    conda install -n {environment_name} -c conda-forge {packages}"
        )
