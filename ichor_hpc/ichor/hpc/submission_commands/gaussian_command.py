from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.core.files import GaussianOutput
from ichor.hpc.global_variables import get_param_from_config

# from ichor.hpc.submission_script.check_manager import CheckManager
from ichor.hpc.submission_command import SubmissionCommand


class GaussianCommand(SubmissionCommand):

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
        ncores: int, 
        gjf_file: Path,
        gjf_output: Optional[Path] = None,
    ):
        self.ncores = ncores
        self.gjf_file = gjf_file
        # .gau file used to store the output from Gaussian
        self.gjf_output = gjf_output or gjf_file.with_suffix(
            GaussianOutput.get_filetype()
        )

    @classproperty
    def modules(self) -> list:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "gaussian",
            "modules",
        )

    @classproperty
    def command(self) -> str:
        """Returns the command used to run Gaussian on different machines."""

        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "gaussian",
            "executable_path",
        )

    @classproperty
    def memory_per_core(self) -> int:
        """Returns the memory per core user wants per Gaussian job"""

        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "hpc",
            "memory_per_core_gb"
        )

    @classmethod
    def total_gaussian_memory(self) -> str:
        """Calculates the total memory to tell Gaussian to use
        Calculated as (memory_per_core - 1) * number_of_cores"""

        mem = (GaussianCommand.memory_per_core-1)*self.ncores

        return mem

    @classproperty
    def group(self) -> bool:
        """Group jobs into an array job."""
        return True

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau).
        This is the data that is going to be written to the datafile."""
        return [str(self.gjf_file.absolute()), str(self.gjf_output.absolute())]

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        The length of `variables` is defined by the length of `self.data`
        """

        # variables[0] ${arr1[$SGE_TASK_ID-1]}, variables[1] ${arr2[$SGE_TASK_ID-1]}
        cmd = f"export GAUSS_SCRDIR=$(dirname {variables[0]})\n{GaussianCommand.command} {variables[0]} {variables[1]}"
        cmd += f"{GaussianCommand.total_gaussian_memory}"

        return cmd
