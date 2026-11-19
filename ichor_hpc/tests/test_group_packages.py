"""Tests for the checks on polus and FEREBUS, the group's own packages.

They are installed separately from ichor, so a new user may well not have them. What
matters is that the menus can say so before a job is submitted, and that the message
says how to get them, rather than the job failing in the queue.
"""

import sys

import pytest

from ichor.hpc.group_packages import (
    FEREBUS,
    GroupPackage,
    GroupPackageMissing,
    is_installed,
    missing_package_warning,
    POLUS,
    require_package,
)

# a package that is certainly installed, as the tests are running with it
PRESENT = GroupPackage(
    name="pytest", module="pytest", repository="pytest", needed_for="testing"
)

# and one that certainly is not
ABSENT = GroupPackage(
    name="nonexistent",
    module="ichor_test_module_that_does_not_exist",
    repository="nonexistent",
    needed_for="nothing at all",
)


def test_an_installed_package_is_found():
    assert is_installed(PRESENT)
    assert missing_package_warning(PRESENT) is None
    require_package(PRESENT, "test job")


def test_a_missing_package_is_warned_about_in_the_menu():
    """The menu warning names the package, and fits on one line of the menu."""

    warning = missing_package_warning(ABSENT)

    assert warning is not None
    assert "nonexistent" in warning
    assert "\n" not in warning


def test_submitting_without_the_package_says_how_to_install_it():
    """The message has to be enough to fix the problem from: where to clone from, and
    the pip to install with, which is the one of the environment the job runs in."""

    with pytest.raises(GroupPackageMissing) as error:
        require_package(ABSENT, "test job")

    message = str(error.value)
    assert "test job" in message
    assert "ichor_test_module_that_does_not_exist" in message
    assert "git clone https://github.com/popelier-group/nonexistent.git" in message
    assert f"{sys.executable} -m pip install -e nonexistent" in message


def test_ferebus_is_checked_for_by_the_module_its_scripts_import():
    """The repository is FEREBUS_CPU, but the training scripts import pyferebus, and it is
    the import that has to succeed."""

    assert FEREBUS.module == "pyferebus"
    assert FEREBUS.clone_url.endswith("/FEREBUS_CPU.git")


def test_polus_is_checked_for_by_the_module_its_scripts_import():
    assert POLUS.module == "polus"
