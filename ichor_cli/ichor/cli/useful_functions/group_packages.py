"""Stops a menu submitting a job whose script imports a package that is not installed."""

import ichor.hpc.global_variables
from ichor.cli.useful_functions.summary import print_summary_and_pause
from ichor.hpc.group_packages import GroupPackage, GroupPackageMissing, require_package


def group_package_installed(
    package: GroupPackage, job_description: str, not_submitted_title: str
) -> bool:
    """Checks that ``package`` is installed in ichor's own environment, where the job
    about to be submitted runs, and tells the user how to install it if it is not.

    Called before anything is written, so that a job which can only fail once it
    starts is neither written out nor left waiting in the queue.

    :param package: The package the job's script imports.
    :param job_description: What is about to be submitted, e.g.
        ``diversity sampling job``.
    :param not_submitted_title: The title of the summary shown if it is missing.
    :return: Whether the package is installed, and so whether to go ahead.
    """

    try:
        require_package(package, job_description)
    except GroupPackageMissing as error:
        ichor.hpc.global_variables.LOGGER.error(
            f"{not_submitted_title.capitalize()}: {error}"
        )
        print_summary_and_pause(
            not_submitted_title,
            {
                "Missing package": (
                    package.name
                    if package.name == package.module
                    else f"{package.name} (imported as {package.module})"
                ),
                "Needed for": package.needed_for,
            },
            [
                str(error),
                "Nothing has been written or submitted. Once it is installed, submit "
                "again from this menu.",
            ],
        )
        return False

    return True
