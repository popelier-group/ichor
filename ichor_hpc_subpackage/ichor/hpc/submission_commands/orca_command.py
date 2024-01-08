from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.core.files import OrcaOutput
from ichor.hpc.modules import Modules, OrcaModules

# from ichor.hpc.submission_script.check_manager import CheckManager
from ichor.hpc.submission_command import SubmissionCommand, SubmissionError


class OrcaCommand(SubmissionCommand):

    """
    A class which is used to add Gaussian-related commands to a submission script.
    It is used to write the submission script line where Gaussian modules are loaded.
    It is also used to write out the submission script line where Gaussian is ran on a
    specified array of files (usually Gaussian is ran as an array job because we want to
    run hundreds of Gaussian tasks in parallel).

    :param gjf_file: Path to a gjf file. This is not needed when running auto-run for a whole directory.
    :param gjf_output: Optional path to the Gaussian job output for the gjf_file.
        Default is None as it is set to the `gjf_file_name`.gau if not specified.
    """

    def __init__(
        self,
        orca_input: Path,
        orca_output: Optional[Path] = None,
    ):
        self.orca_input = orca_input
        self.orca_output = orca_output or orca_input.with_suffix(OrcaOutput.filetype)

    @classproperty
    def command(self) -> str:
        """Returns the command used to run ORCA on different machines."""

        if (
            ichor.hpc.global_variables.MACHINE
            not in ichor.hpc.global_variables.ORCA_COMMANDS.keys()
        ):
            raise SubmissionError(
                f"Command not defined for '{self.__name__}' on '{ichor.hpc.global_variables.MACHINE.name}'"
            )

        return ichor.hpc.global_variables.ORCA_COMMANDS[
            ichor.hpc.global_variables.MACHINE
        ]

    @classproperty
    def modules(self) -> Modules:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return OrcaModules

    @classproperty
    def group(self) -> bool:
        """Group jobs into an array job."""
        return True

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the ORCA input file (.orcainput) and the output file (.gau).
        This is the data that is going to be written to the datafile."""
        return [str(self.orca_input.absolute()), str(self.orca_output.absolute())]

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        The length of `variables` is defined by the length of `self.data`
        """

        # variables[0] ${arr1[$SGE_TASK_ID-1]}, variables[1] ${arr2[$SGE_TASK_ID-1]}
        cmd = f"\n{OrcaCommand.command} {variables[0]} > {variables[1]}"

        return cmd
