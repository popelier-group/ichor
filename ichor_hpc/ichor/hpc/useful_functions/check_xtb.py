"""Preflight check for the `xtb` package used by the ASE optimisation jobs.

The scripts ichor generates for ASE optimisations do `from xtb.ase.calculator import XTB`,
and they are ran by `PythonCommand`, which activates the same Python environment that ichor
itself is running from. If `xtb` is not installed in that environment, the submitted jobs
all fail at run time with a `ModuleNotFoundError` that is only visible in the job's error
file. Checking on the login node before submitting turns that into an immediate,
actionable error instead.

Note this check is only meaningful for the jobs submitted with `PythonCommand`. The
metadynamics jobs use `AnacondaCommand`, which activates a separately configured conda
environment (`software.python.env_name` in the ichor config file) rather than ichor's own,
so `xtb` being importable here says nothing about whether those jobs will work.
"""

import importlib.util
import sys

# the environment is looked up through this function rather than through
# `ichor.hpc.global_variables.CURRENT_PYTHON_ENVIRONMENT_PATH` (which is the same thing)
# because `global_variables` imports this package, so importing it here would be circular
from ichor.hpc.useful_functions.get_python_environment import (
    get_current_python_environment_path,
)


class XTBNotFound(Exception):
    pass


def xtb_is_installed() -> bool:
    """Returns whether the `xtb` package is importable in the environment ichor is
    running from. The module is not imported, only located."""

    return importlib.util.find_spec("xtb") is not None


def _current_environment_description() -> str:
    """Returns a human readable description of the Python environment that the
    submitted jobs are going to activate."""

    python_env = get_current_python_environment_path()

    if python_env.uses_venv:
        return f"the venv environment at {python_env.venv_path}"
    elif python_env.uses_conda:
        return f"the conda environment at {python_env.conda_path}"

    return "the current Python environment"


def _how_to_install_xtb() -> str:
    """Returns instructions for installing xtb into the environment ichor is running
    from. The PyPI wheels only exist for CPython 3.11 and older, so on newer
    interpreters the only option is conda-forge (which needs ichor to be in a conda
    environment) or moving ichor to an older interpreter."""

    python_env = get_current_python_environment_path()

    if sys.version_info < (3, 12):
        return "Install it into that environment with `python3 -m pip install xtb`."

    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    no_wheel = f"The xtb wheels on PyPI do not support Python {version}, so pip cannot "

    # a venv is reported even when a conda environment is also active, because that is
    # the one `PythonCommand` activates, and conda-forge packages cannot go into a venv
    if python_env.uses_venv:
        return (
            f"{no_wheel}install it, and conda-forge packages cannot be installed into "
            "a venv. Run ichor from a Python 3.11 environment (where "
            "`python3 -m pip install xtb` works), or from a conda environment with "
            "`conda install -c conda-forge xtb-python`."
        )

    elif python_env.uses_conda:
        return (
            f"{no_wheel}install it. Install it into that conda environment instead "
            "with `conda install -c conda-forge xtb-python`."
        )

    return (
        f"{no_wheel}install it. Run ichor from a Python 3.11 environment (where "
        "`python3 -m pip install xtb` works), or from a conda environment with "
        "`conda install -c conda-forge xtb-python`."
    )


def check_xtb_is_installed() -> None:
    """Raises if the `xtb` package is not importable in the environment ichor is running
    from, as the ASE optimisation scripts that are about to be submitted import it.

    :raises XTBNotFound: If `xtb` is not installed in ichor's Python environment.
    """

    if xtb_is_installed():
        return

    raise XTBNotFound(
        "The xtb package is not installed in "
        f"{_current_environment_description()}, which is the environment the "
        "submitted ASE optimisation jobs activate, so every job would fail with "
        "`ModuleNotFoundError: No module named 'xtb'`. "
        f"{_how_to_install_xtb()}"
    )
