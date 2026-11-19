"""Checks for the group's own packages, polus and FEREBUS, which some jobs need.

Both are kept in private repositories on the popelier-group GitHub organisation, so
they cannot be dependencies of ichor and are installed separately. The scripts ichor
writes for diversity sampling and dataset preparation import polus, and the ones it
writes for model training import pyferebus, and all of them run in ichor's own Python
environment. Without these checks a missing package is only found when the job dies
with a ``ModuleNotFoundError`` in an error file, after it has waited in the queue.

As the jobs run in the environment ichor itself is running from, whether a package is
there can be checked in this process, unlike the conda environment of the ASE jobs
(see ``ichor.hpc.check_python_env``).
"""

import importlib.util
import sys

from dataclasses import dataclass
from typing import Optional

# where the group's repositories are, which is also where access to them is granted
GROUP_GITHUB = "https://github.com/popelier-group"


class GroupPackageMissing(Exception):
    """A package that the jobs about to be submitted import is not installed in the
    Python environment that ichor is running from."""


@dataclass(frozen=True)
class GroupPackage:
    """One of the group's packages that ichor writes scripts for.

    :param name: What the package is called, as people refer to it.
    :param module: The top level module the generated scripts import.
    :param repository: The name of its repository on the group's GitHub organisation,
        which is also the directory ``git clone`` makes.
    :param needed_for: What it is needed for, e.g. ``model training``.
    """

    name: str
    module: str
    repository: str
    needed_for: str

    @property
    def clone_url(self) -> str:
        return f"{GROUP_GITHUB}/{self.repository}.git"


POLUS = GroupPackage(
    name="polus",
    module="polus",
    repository="POLUS",
    needed_for="diversity sampling and dataset preparation",
)

FEREBUS = GroupPackage(
    name="FEREBUS",
    module="pyferebus",
    repository="FEREBUS_CPU",
    needed_for="model training",
)


def is_installed(package: GroupPackage) -> bool:
    """Whether ``package`` can be imported in the environment ichor is running from.

    find_spec locates the module without importing it, which is quick (the menus call
    this every time they are drawn) and avoids any side effects of importing it.
    """

    return importlib.util.find_spec(package.module) is not None


def how_to_install(package: GroupPackage) -> str:
    """Returns the commands that install ``package`` into ichor's own environment."""

    return (
        f"{package.name} is a private repository on the popelier-group GitHub "
        "organisation, so you need access to it. Then install it into the "
        "environment ichor is running from with:\n\n"
        f"    git clone {package.clone_url}\n"
        f"    {sys.executable} -m pip install -e {package.repository}"
    )


def missing_package_warning(package: GroupPackage) -> Optional[str]:
    """Returns a one line warning for a menu if ``package`` is not installed, and None
    if it is, so that it can be returned straight from a menu's check function."""

    if is_installed(package):
        return None

    return (
        f"{package.name} is not installed in this Python environment, so jobs from "
        "this menu would fail. Submitting says how to install it."
    )


def require_package(package: GroupPackage, job_description: str) -> None:
    """Checks that ``package`` is installed before jobs that import it are written or
    submitted.

    :param package: The package the jobs import.
    :param job_description: What is about to be submitted, used in the message.
    :raises GroupPackageMissing: If the package is not installed.
    """

    if is_installed(package):
        return

    raise GroupPackageMissing(
        f"{package.module} is not installed in the Python environment ichor is running "
        f"from ({sys.executable}), so the {job_description} would only fail with a "
        "ModuleNotFoundError once started.\n\n" + how_to_install(package)
    )
