from pathlib import Path
from typing import List, Optional

from ichor.ichor_lib.common.functools import classproperty
from ichor.modules import GaussianModules, Modules
from ichor.submission_script.check_manager import CheckManager
from ichor.submission_script.command_line import CommandLine, SubmissionError


class GaussianCommand(CommandLine):

    """
    A class which is used to add Gaussian-related commands to a submission script. It is used to write the submission script line where
    Gaussian modules are loaded. It is also used to write out the submission script line where Gaussian is ran on a specified array of files (usually
    Gaussian is ran as an array job because we want to run hundreds of Gaussian tasks in parallel). Finally, depending on the `check` and `scrub` arguments,
    additional lines are written to the submission script file which rerun failed tasks as well as remove any points that did not terminate normally (even
    after being reran).

    :param gjf_file: Path to a gjf file. This is not needed when running auto-run for a whole directory.
    :param gjf_output: Optional path to the Gaussian job output for the gjf_file. Default is None as it is set to the `gjf_file_name`.gau if not specified.
    """

    def __init__(
        self,
        gjf_file: Path,
        gjf_output: Optional[Path] = None,
    ):
        self.gjf_file = gjf_file
        self.gjf_output = gjf_output or gjf_file.with_suffix(
            ".gau"
        )  # .gau file used to store the output from Gaussian

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [str(self.gjf_file.absolute()), str(self.gjf_output.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return GaussianModules

    @classproperty
    def command(self) -> str:
        """Returns the command used to run Gaussian on different machines."""
        from ichor.ichor_hpc.machine_setup.machine_setup import MACHINE, Machine

        if MACHINE is Machine.csf3:
            return "$g09root/g09/g09"
        elif MACHINE is Machine.ffluxlab:
            return "g09"
        elif MACHINE is Machine.local:
            return "g09_test"
        raise SubmissionError(
            f"Command not defined for '{self.__name__}' on '{MACHINE.name}'"
        )

    @classproperty
    def ncores(self) -> int:
        """Returns the number of cores that Gaussian should use for the job."""
        from ichor.ichor_hpc.globals import GLOBALS

        return GLOBALS.GAUSSIAN_NCORES

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        If the outputs of the job need to be checked (by default self.rerun is set to True, so job outputs are checked),
        then the corresponsing strings are appended to the initial commands string.

        The length of `variables` is defined by the length of `self.data`
        """

        cmd = f"export GAUSS_SCRDIR=$(dirname {variables[0]})\n{GaussianCommand.command} {variables[0]} {variables[1]}"  # variables[0] ${arr1[$SGE_TASK_ID-1]}, variables[1] ${arr2[$SGE_TASK_ID-1]}

        from ichor.ichor_hpc.globals import GLOBALS

        if GLOBALS.RERUN_POINTS:

            cm = CheckManager(
                check_function="rerun_gaussian",
                args_for_check_function=[variables[0]],
                ntimes=GLOBALS.GAUSSIAN_N_TRIES,
            )
            cmd = cm.rerun_if_job_failed(cmd)

        if GLOBALS.SCRUB_POINTS:
            cm = CheckManager(
                check_function="scrub_gaussian",
                args_for_check_function=[variables[0]],
            )
            cmd = cm.scrub_point_directory(cmd)

        return cmd
