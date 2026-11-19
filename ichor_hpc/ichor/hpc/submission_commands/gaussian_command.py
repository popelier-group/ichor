import warnings

from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.core.files import GaussianOutput
from ichor.hpc.global_variables import get_param_from_config

# from ichor.hpc.submission_script.check_manager import CheckManager
from ichor.hpc.submission_command import SubmissionCommand


class MissingGaussianMemorySetting(ValueError):
    """Gaussian memory per core is missing from the HPC configuration."""


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

    @staticmethod
    def memory_per_core(ncores: int) -> int:
        """Returns the memory per core that a Gaussian job on ``ncores`` cores is sized
        around.

        Read from ``hpc.memory_per_core_gb``, which is either one number for the whole
        machine or a mapping from partition (parallel environment) name to the memory a
        core brings on it, e.g. ``{serial: 5, multicore: 8}``. A machine which does not
        set it at all falls back to a small budget and warns, rather than failing with a
        TypeError when the missing value reaches the arithmetic below. The fallback is
        deliberately conservative: asking for more memory than a core actually brings
        gets the job killed on the node.

        :raises MissingGaussianMemorySetting: if a mapping is given but has no entry for
            the partition a job on ``ncores`` cores is sent to.
        """

        machine = ichor.hpc.global_variables.MACHINE
        partition_memory = get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            machine,
            "hpc",
            "memory_per_core_gb",
        )

        if partition_memory is None:
            warnings.warn(
                "hpc.memory_per_core_gb is not set for this machine in "
                f"{ichor.hpc.global_variables.CONFIG_DESCRIPTION}, so Gaussian jobs "
                "are being sized with an assumed "
                f"{ichor.hpc.global_variables.DEFAULT_MEMORY_PER_CORE_GB} GB per "
                "core. Set it to what a core actually brings on this machine, or "
                "jobs may ask for more memory than they are given."
            )
            return ichor.hpc.global_variables.DEFAULT_MEMORY_PER_CORE_GB

        if isinstance(partition_memory, dict):
            partition = ichor.hpc.global_variables.PARALLEL_ENVIRONMENT[ncores]
            memory = partition_memory.get(partition)
            if memory is None:
                raise MissingGaussianMemorySetting(
                    f"hpc.memory_per_core_gb has no entry for partition {partition!r} "
                    f"on machine {machine!r} in "
                    f"{ichor.hpc.global_variables.CONFIG_DESCRIPTION}."
                )
            return memory

        return partition_memory

    @classmethod
    def memory_for_cores(cls, ncores: int) -> int:
        """Return Gaussian memory in GB, leaving 1 GB of headroom per core."""
        return (cls.memory_per_core(ncores) - 1) * ncores

    def total_gaussian_memory(self) -> str:
        """Return the shell directive setting Gaussian's default memory."""
        return f"export GAUSS_MDEF={self.memory_for_cores(self.ncores)}GB"

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
        cmd = f"export GAUSS_SCRDIR=$(dirname {variables[0]})"
        cmd += f"\n{self.total_gaussian_memory()}"
        # the number of cores the job was given, which the batch system puts in a
        # variable of its own (NSLOTS on SGE, SLURM_CPUS_PER_TASK on SLURM). It used to
        # be SLURM_NTASKS, which is empty on SGE and, now that the cores are asked for
        # with --cpus-per-task, would be 1 on SLURM and make Gaussian run on one core.
        cmd += (
            "\nexport GAUSS_PDEF="
            f"${ichor.hpc.global_variables.BATCH_SYSTEM.NumProcs}"
        )
        cmd += f"\n{GaussianCommand.command} {variables[0]} {variables[1]}"
        return cmd
