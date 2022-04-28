from typing import List, Optional, Tuple

from ichor.modules import Modules
from ichor.submission_script.command_line import CommandLine


class CommandGroup(CommandLine, list):
    """Wraps around jobs that are of the same type, i.e. Gaussian jobs, AIMALL jobs, FEREBUS jobs, ICHOR jobs.
    Since each job uses the same settings, we can just use the 0th index."""

    @property
    def command(self) -> str:
        """Returns a string containing the command which is going to be ran (eg. g09 for Gaussian on CSF3.)"""
        return self[0].command

    @property
    def ncores(self) -> int:
        """Returns the number of cores to be used for the job or each task in a job array."""
        return self[0].ncores

    @property
    def data(self) -> Tuple[str]:
        """Returns the data that a job needs.
        This is usually a set of files which are the input files and the output files to be written by the job."""
        return self[0].data

    @property
    def modules(self) -> Modules:
        """Retruns a string containing any modules that need to be loaded in order for a program to run"""
        return self[0].modules

    @property
    def arguments(self) -> List[str]:
        """Returns the arguments (if any) that need to be passed to the program that the job is going to execute."""
        return self[0].arguments

    @property
    def options(self) -> List[str]:
        """Returns the options to write at the top of the submission script"""
        return self[0].options

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Return a string which represents the line in the job script which runs the program (Gaussian, AIMALL, etc.) with
        its given inputs (typically these inputs are in the form of a job array so they look like ${arr1[$SGE_TASK_ID-1]}"""
        return self[0].repr(variables)
