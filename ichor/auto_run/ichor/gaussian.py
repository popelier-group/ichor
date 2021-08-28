from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)

# matt_todo: rename autorun files and functions to make them easier to understand
# runs on login node when doing autorun
def submit_gjfs(directory, hold: Optional[JobID] = None) -> Optional[JobID]:
    """ Writes out datafile that is needed for the Gaussian jobs. The actual Gaussian calculations run with the next job in the auto run sequence,
    but they need access to the datafile. This is why the datafile needs to be written prior to actually running the Gaussian job.
    
    .. note::
        The `submit_gjfs` that runs is NOT this function. The `submit_gjfs` function that runs is the one as defined in `Arguments.import_external_functions()`.
        The `submit_gjfs` function that runs writes out the datafiles needed for the Gaussian jobs, but does not actually run Gaussian in autorun because in
        autorun, it is called from a compute node, so it does not submit.

    """

    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["gaussian"])
    ichor_command = ICHORCommand()  # which command to run in the job script
    ichor_command.run_function("submit_gjfs", str(directory))  # extend the command with arguments
    with TimingManager(submission_script, message="Submitting GJFs"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)  # gives back job id
