from pathlib import Path
from typing import Optional, Union

from ichor.batch_system import JobID
from ichor.common.types import MutableValue
from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def submit_ichor_gaussian_command_to_auto_run(
    directory: Union[Path, MutableValue], force: Optional[MutableValue] = None, hold: Optional[JobID] = None
) -> Optional[JobID]:
    """Writes out datafile that is needed for the Gaussian jobs. The actual Gaussian calculations run with the next job in the auto run sequence,
    but they need access to the datafile. This is why the datafile needs to be written prior to actually running the Gaussian job.

    .. note::
        The `submit_gjfs` that runs is NOT this function. The `submit_gjfs` function that runs is the one as defined in `Arguments.import_external_functions()`.
        The `submit_gjfs` function that runs writes out the datafiles needed for the Gaussian jobs, but does not actually run Gaussian in autorun because in
        autorun, it is called from a compute node, so it does not submit.

    """
    if isinstance(directory, MutableValue):
        directory = directory.value
    if isinstance(force, MutableValue):
        force = force.value
    if force is None:
        force = False

    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["gaussian"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job(
        submit_points_directory_to_gaussian, str(directory), True, force
    )
    with TimingManager(submission_script, message="Sumitting GJFs"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
