from pathlib import Path
from typing import List, Optional, Tuple

from ichor.batch_system import BATCH_SYSTEM, JobID
from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.common.types import BoolToggle
from ichor.common.uid import set_uid
from ichor.machine import MACHINE, SubmitType
from ichor.submission_script.command_group import CommandGroup
from ichor.submission_script.data_lock import DataLock

SUBMIT_ON_COMPUTE = BoolToggle(False)


class SubmissionScript:
    """
    A class that can be used to construct submission scripts for various programs such as Gaussian and AIMALL.
    :param path: A path to a submission script (such as GAUSSIAN.sh and AIMALL.sh). These .sh files are submitted as jobs to CSF3/FFLUXLAB.
    These job scripts will have different contents depending on the number of cores selected, the number of tasks to do (if running an array job), etc.,
    so they need to be written out dynamically depending on what is going to be ran.
    """

    SEPARATOR = ","  # separator which is used to separate names of files in the datafiles (files with random UID names) which are written by ICHOR.
    DATAFILE = "ICHOR_DATFILE"  # name of the bash variable which is used to store the location of the datafile for the given job.

    def __init__(self, path: Path):
        self.path = Path(path)
        self.commands = (
            []
        )  # a list of commands to be submitted to batch system
        self._ncores = None

    @classproperty
    def filetype(self) -> str:
        """The extension of the submission script file. Will always be .sh (a shell script)"""
        return ".sh"

    def add_command(self, command):
        """Add a command to the list of commands."""
        self.commands += [command]

    @property
    def ncores(self) -> int:
        """Number of cores to be used for the job."""
        return self._ncores or max(
            command.ncores for command in self.grouped_commands
        )

    @ncores.setter
    def ncores(self, ncores: int):
        self._ncores = ncores

    @property
    def default_options(self) -> List[str]:
        """Returns a list of default options to use in a submission script for a job.
        This list contaning the current working directory, the output directory (where .o files are written),
        the errors directory (where .e files are witten). If the number of cores is more than 1, the keyword
        needed when specifying more than 1 cores is also written to the options list. This keyword depends on
        the system on which the job is ran, as well as on the number of cores that the job needs."""
        from ichor.file_structure import FILE_STRUCTURE
        from ichor.globals import GLOBALS

        mkdir(FILE_STRUCTURE["outputs"])
        mkdir(FILE_STRUCTURE["errors"])

        # change current working directory to directory from which ICHOR is launched.
        # make the paths to outputs and errors absolute
        options = [
            BATCH_SYSTEM.change_working_directory(GLOBALS.CWD),
            BATCH_SYSTEM.output_directory(FILE_STRUCTURE["outputs"].resolve()),
            BATCH_SYSTEM.error_directory(FILE_STRUCTURE["errors"].resolve()),
        ]

        # if the number of cores is more than 1, have to add additional options
        if self.ncores > 1:
            options += [BATCH_SYSTEM.parallel_environment(self.ncores)]

        return options

    @property
    def options(self) -> List[str]:
        """Return the complete list of options (default options + other options that are specific to the job)."""
        options = []
        for command in self.grouped_commands:
            options += command.options
        # do not duplicate commands
        return list(set(options + self.default_options))

    @property
    def modules(self) -> List[str]:
        """Returns a list of modules that need to be loaded before a job can be ran."""
        from ichor.machine import MACHINE

        modules = []
        for command in self.grouped_commands:
            modules += command.modules[
                MACHINE
            ]  # modules depend on which machine (CSF/FFLUXLAB) we are currently on
        return list(set(modules))

    @property
    def grouped_commands(self) -> List[CommandGroup]:
        """
        Group commands if they need to be submitted into an array job. These commands will all be the same type, i.e. they
        will all be Gaussian jobs, or AIMALL jobs. Sometimes ICHOR needs to be ran after the job is complete (for example ICHOR needs
        to be ran after a FEREBUS job in order to do adaptive sampling).

        e.g. if we had a list of commands like the following:
        [Gaussian, Gaussian, Ichor, AIMAll, AIMAll]
        The commands will be grouped by type:
        [[Gaussian, Gaussian], [Ichor], [AIMAll, AIMAll]]

        The groupings are then used to allocate a task array to the batch system
        """
        commands = []
        command_group = CommandGroup()  # make a new command group
        command_type = None

        # iterate over each command instance that has been added to self.commands
        for command in self.commands:
            # if the command is not equal to command_type or commands.group is set to False (group method defined in CommandLine class, default True)
            if (
                type(command) != command_type or not command.group
            ):  # .group flag used by command if it doesn't want to be grouped
                if (
                    len(command_group) > 0
                ):  # just for first iteration of the loop
                    commands += [command_group]
                    command_group = CommandGroup()
                command_type = type(command)
            command_group += [command]

        if len(command_group) > 0:
            commands += [command_group]
        return commands

    @classmethod
    def arr(cls, n):
        """Returns the keyword which is used to select array jobs. Since array jobs start at 1 instead of 0, 1 needs to be added
        to the array size."""
        return f"arr{n + 1}"

    @classmethod
    def array_index(cls, n):
        """Returns the keywords used to run an array job through a program such as Gaussian.

        .. note::
            For example, this line in GAUSSIAN.sh (the submission script for Gaussian) is
            g09 ${arr1[$SGE_TASK_ID-1]} ${arr2[$SGE_TASK_ID-1]}
            The g09 is the program (however this depend on which system you are on). The rest is what is returned by this method.
        """
        # Note: double {{ }} is python notation for writing a curly brace in an f-string
        return f"${{{cls.arr(n)}[${BATCH_SYSTEM.TaskID}-1]}}"

    @classmethod
    def var(cls, n):
        return f"var{n + 1}"

    def write_datafile(self, datafile: Path, data: List[List[str]]) -> None:
        """Write the datafile to disk. All datafiles are stored in GLOBALS.FILE_STRUCTURE["datafiles"]. Each line of the
        datafile contains text that corresponds to the inputs and output file names. These are separated by self.separator, which is a comma.

        .. note::
            For example, a datafile, which has a random name (which is the GLOBALS.UID) contains lines in the form of:
            WATER0001.gjf,WATER0001.gau
            WATER0002.gjf,WATER0002.gau
            ...
        """
        if not DataLock.locked:
            mkdir(datafile.parent)
            with open(datafile, "w") as f:
                for cmd_data in data:
                    # Note: cmd_data should already be strings but we will perform a map just to be safe
                    f.write(
                        f"{SubmissionScript.SEPARATOR.join(map(str, cmd_data))}\n"
                    )

    def setup_script_arrays(
        self, datafile: Path, data: List[List[str]]
    ) -> str:
        """Forms the strings for array jobs which are then written to the submission script to specify the number of
        tasks in the array job and things like that. Easiest to see if you have GAUSSIAN.sh or another submission script opened.
        """

        # number of files needeed for one of the tasks in the array job
        ndata = len(data[0])

        # absolute location of datafile on disk
        datafile_str = f"{SubmissionScript.DATAFILE}={datafile.absolute()}"

        # writes out the number of arrays needed for the job
        # Note: implemented as generator so that a list generation and comprehension is not required
        read_datafile_str = "".join(
            f"{self.arr(i)}=()\n" for i in range(ndata)
        )

        # writes out the while loop needed to read in files names into their corresponding arrays
        # -r option prevents backslashes from being treated as escape characters
        read_datafile_str += (
            f"while IFS={SubmissionScript.SEPARATOR} read -r "
            f"{' '.join(self.var(i) for i in range(ndata))}\n"
        )
        read_datafile_str += "do\n"
        for i in range(ndata):
            read_datafile_str += f"    {self.arr(i)}+=(${self.var(i)})\n"
        read_datafile_str += f"done < ${SubmissionScript.DATAFILE}\n"

        return f"{datafile_str}\n{read_datafile_str}"

    def setup_datafile(
        self, datafile: Path, data: List[List[str]]
    ) -> Tuple[List[str], str]:
        """Calls write_datafile which writes the datafile to disk (if it is not locked). Then it reads

        :param datafile: Path object that points to a datafile location (which is going to be written now by write_datafile)
        :param data: A list of lists. Each inner list contains strings which are the names of the inputs and output files.
        """
        self.write_datafile(datafile, data)
        datafile_str = self.setup_script_arrays(datafile, data)
        datafile_variables = [self.array_index(i) for i in range(len(data[0]))]
        set_uid()
        return datafile_variables, datafile_str

    def write(self):
        """Writes the submission script that is passed to the queuing system. The options for the job (such as directory, number of jobs, core count, etc.)
        are written at the top of the file. The commands to run (such as Gaussian, AIMALL, etc.) are written below the options."""
        from ichor.file_structure import FILE_STRUCTURE
        from ichor.globals import GLOBALS

        mkdir(self.path.parent)

        with open(self.path, "w") as f:

            njobs = max(
                len(command_group) for command_group in self.grouped_commands
            )

            f.write("#!/bin/bash -l\n")
            # write any options to be given to the batch system, such as working directory, where to write outputs/errors, etc.
            for option in self.options:
                f.write(f"#{BATCH_SYSTEM.OptionCmd} {option}\n")
            # if writing an array jobs, then the batch system needs to know that
            # on SGE, this is given by the #$ -t 1-{njobs}. SGE starts counting from 1 instead of 0.
            if GLOBALS.INCLUDE_NODES or GLOBALS.EXCLUDE_NODES:
                f.write(
                    f"#{BATCH_SYSTEM.OptionCmd} {BATCH_SYSTEM.node_options(GLOBALS.INCLUDE_NODES, GLOBALS.EXCLUDE_NODES)}\n"
                )
            if njobs > 1:
                f.write(
                    f"#{BATCH_SYSTEM.OptionCmd} {BATCH_SYSTEM.array_job(njobs)}\n"
                )
                if njobs > GLOBALS.MAX_RUNNING_TASKS > 0:
                    f.write(
                        f"#{BATCH_SYSTEM.OptionCmd} {BATCH_SYSTEM.max_running_tasks(GLOBALS.MAX_RUNNING_TASKS)}\n"
                    )
            else:
                f.write(f"{BATCH_SYSTEM.TaskID}=1\n")

            # if job or array job is going to use more than 1 cores, then we need extra things to write.
            if self.ncores > 1:
                f.write(f"export OMP_NUM_THREADS={self.ncores}\n")
                # f.write(f"export OMP_PROC_BIND=spread\n")
                # f.write(f"export OMP_PLACES=cores\n")

            # load any modules required for the job
            for module in self.modules:
                f.write(f"module load {module}\n")

            for command_group in self.grouped_commands:
                command_variables = []
                if (
                    command_group.data
                ):  # Gaussian, Ferebus, AIMALL jobs need access to datafiles, the datfile's name is the unique id that was assigned to GLOBALS
                    datafile = FILE_STRUCTURE["datafiles"] / Path(
                        str(GLOBALS.UID)
                    )
                    # get the data that is needed for each command in a command group
                    # for example, if the command is a Gaussian command, then we need an input file (.gjf) and an output file (.gau)
                    # command_group_data is a list of lists. Each inner list has input/output files
                    command_group_data = [
                        command.data for command in command_group
                    ]
                    # datafile_vars is a list of strings corresponding to the arrays that need to be used by the program we are running (eg. Gaussian)
                    # datafile_str is the rest of the stuff that sets up the arrays used for the array job in the submission script
                    datafile_vars, datafile_str = self.setup_datafile(
                        datafile, command_group_data
                    )
                    command_variables += datafile_vars
                    f.write(
                        f"{datafile_str}\n"
                    )  # write the array job parts to the submission script
                f.write(
                    f"{command_group.repr(command_variables)}\n"
                )  # see class GaussianCommand for example

    def submit(self, hold: Optional[JobID] = None) -> Optional[JobID]:
        from ichor.batch_system import BATCH_SYSTEM, NodeType

        if (
            BATCH_SYSTEM.current_node() is not NodeType.ComputeNode
            or SUBMIT_ON_COMPUTE
            and MACHINE.submit_type is SubmitType.SubmitOnCompute
        ):
            return BATCH_SYSTEM.submit_script(self.path, hold)

    def __enter__(self) -> "SubmissionScript":
        """
        Allows for syntax such as
        ```python
        with SubmissionScript(...) as submission_script:
            ...
        ```
        :return self: SubmissionScript instance used during context
        """
        return self

    # Note: arguments of __exit__ statement are required
    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Writes out the submission script once the `with` context manager is done. The exc_type, exc_val, exc_tb are needed for every __exit__ method.

        :param exception_type: If an exception has ocurred during the context, the write method will not be executed
        :param exception_value: Not used
        :param exception_traceback: Not used

        .. note::
            This does not submit the submission script, it only writes it to disk.
        """
        if exception_type is None:
            self.write()
