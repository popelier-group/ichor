from pathlib import Path
from typing import List, Optional, Tuple

from ichor.batch_system import BATCH_SYSTEM, JobID
from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.common.uid import set_uid
from ichor.submission_script.command_group import CommandGroup
from ichor.submission_script.data_lock import DataLock


class SubmissionScript:
    """
    A class that can be used to construct submission scripts for various programs such as Gaussian and AIMALL.
    :param path: A path to a submission script (such as GAUSSIAN.sh and AIMALL.sh). These .sh files are submitted as jobs to CSF3/FFLUXLAB.
    These job scripts will have different contents depending on the number of cores selected, the number of tasks to do (if running an array job), etc.,
    so they need to be written out dynamically depending on what is going to be ran.
    """
    def __init__(self, path: Path):
        self.path = Path(path)
        self.commands = []  # a list of commands to be submitted to batch system

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
        return max(command.ncores for command in self.grouped_commands)

    @property
    def default_options(self) -> List[str]:
        """ Returns a list of default options to use in a submission script for a job.
        This list contaning the current working directory, the output directory (where .o files are written),
        the errors directory (where .e files are witten). If the number of cores is more than 1, the keyword
        needed when specifying more than 1 cores is also written to the options list. This keyword depends on
        the system on which the job is ran, as well as on the number of cores that the job needs."""
        from ichor.globals import GLOBALS

        mkdir(GLOBALS.FILE_STRUCTURE["outputs"])
        mkdir(GLOBALS.FILE_STRUCTURE["errors"])

        # change current working directory to directory from which ICHOR is launched.
        # make the paths to outputs and errors absolute
        options = [
            BATCH_SYSTEM.change_working_directory(GLOBALS.CWD),
            BATCH_SYSTEM.output_directory(
                GLOBALS.FILE_STRUCTURE["outputs"].resolve()
            ),
            BATCH_SYSTEM.error_directory(
                GLOBALS.FILE_STRUCTURE["errors"].resolve()
            ),
        ]

        # if the number of cores is more than 1, have to add additional options
        if self.ncores > 1:
            options += [BATCH_SYSTEM.parallel_environment(self.ncores)]

        return options

    @property
    def options(self) -> List[str]:
        """ Return the complete list of options (default options + other options that are specific to the job). """
        options = []
        for command in self.grouped_commands:
            options += command.options
        # do not duplicate commands
        return list(set(options + self.default_options))

    @property
    def modules(self) -> List[str]:
        """ Returns a list of modules that need to be loaded before a job can be ran. """
        from ichor.globals import GLOBALS

        modules = []
        for command in self.grouped_commands:
            modules += command.modules[GLOBALS.MACHINE] # modules depend on which machine (CSF/FFLUXLAB) we are currently on
        return list(set(modules))

    def group_commands(self) -> List[CommandGroup]:
        """ Group commands if they need to be submitted into an array job. These commands will all be the same type, i.e. they
        will all be Gaussian jobs, or AIMALL jobs. Sometimes ICHOR needs to be ran after the job is complete (for example ICHOR needs
        to be ran after a FEREBUS job in order to do adaptive sampling). """
        commands = []
        command_group = CommandGroup()  # make a new command group
        command_type = None
        # matt_todo: not really sure what this  is doing. Is this to make a group of Gaussian jobs for example to run in a job array?
        # matt_todo: also command.group is only defined for ICHORCommand jobs. Maybe then modify the for loop to be more explicit.
        # iterate over each command instance that has been added to self.commands
        for command in self.commands:
            # if the command is not equal to command_type or commands.group is set to False (group method defined in CommandLine class, default True)
            if type(command) != command_type or not command.group:
                if len(command_group) > 0:  # just for first iteration of the loop
                    commands += [command_group]
                    command_group = CommandGroup()
                command_type = type(command)
            command_group += [command]
        # commands = [[GaussianCommand(), GaussianCommand()]]
        if len(command_group) > 0:
            commands += [command_group]
        return commands

        # ICHOR_SUBMIT_GJF
        # GAUSSIAN commands
        # ICHOR_SUBMIT_WFNS
        # AIMALL commands

    # matt_todo: why is a separate method needed? Make the top group_commands method into a property and rename it so there are not two methods
    @property
    def grouped_commands(self):
        return self.group_commands()

    # matt_todo: These just return constant things, so there is no need for classproperty here I think. Can make into class variables
    @classproperty
    def separator(self):
        """ Returns the separator which is used to separate names of files in the datafiles (files with random UID names)
        which are written by ICHOR."""
        return ","

    @classproperty
    def datafile_var(self) -> str:
        """ Returns the name of the variable which is used to store the location of the datafile for the given job."""
        return "ICHOR_DATFILE"

    @classmethod
    def arr(cls, n):
        """ Returns the keyword which is used to select array jobs. Since array jobs start at 1 instead of 0, 1 needs to be added
        to the array size. """
        return f"arr{n + 1}"

    @classmethod
    def array_index(cls, n):
        """ Returns the keywords used to run an array job through a program such as Gaussian.

        .. note::
            For example, this line in GAUSSIAN.sh (the submission script for Gaussian) is
            g09 ${arr1[$SGE_TASK_ID-1]} ${arr2[$SGE_TASK_ID-1]}
            The g09 is the program (however this depend on which system you are on). The rest is what is returned by this method.
        """
        # matt_todo: pretty sure you do not need two of the {{ }} on each side
        return f"${{{cls.arr(n)}[${BATCH_SYSTEM.TaskID}-1]}}"

    @classmethod
    def var(cls, n):
        return f"var{n + 1}"

    def write_datafile(self, datafile: Path, data: List[List[str]]) -> None:
        """ Write the datafile to disk. All datafiles are stored in GLOBALS.FILE_STRUCTURE["datafiles"]. Each line of the
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
                    # matt_todo: self.separator should be SubmissionScript.separator because separator is a class property
                    # matt_todo: not sure if the map is needed as you have made them strings in GaussianCommand.data anyway, so they
                    # should already be strings
                    f.write(f"{self.separator.join(map(str, cmd_data))}\n")

    # matt_todo: I this this method could be renamed and some of the variables as well, because it doesn't really read a datafile string,
    # matt_todo: it just construct the strings needed to make the arrays for the datafiles
    # matt_todo: maybe call it setup_script_arrays or something like that
    def read_datafile_str(self, datafile: Path, data: List[List[str]]) -> str:
        """ Forms the strings for array jobs which are then written to the submission script to specify the number of 
        tasks in the array job and things like that. Easiest to see if you have GAUSSIAN.sh or another submission script opened.
        """
        # matt_todo: make used of classproperty so SubmissionScript.datafile_var instead of self.datafile_var. I think that will make it easier to read
        # matt_todo: really I think some of these can be made into class variables since they are constant, no need of classproperty here

        # number of files needeed for one of the tasks in the array job
        ndata = len(data[0])

        # absolute location of datafile on disk
        datafile_str = f"{self.datafile_var}={datafile.absolute()}"

        # writes out the number of arrays needed for the job
        # matt_todo: since using a for loop below, maybe use a for loop here as well to make it more readable
        read_datafile_str = "".join(
            f"{self.arr(i)}=()\n" for i in range(ndata)
        )
        
        # writes out the while loop needed to read in files names into their corresponding arrays
        # -r option prevents backslashes from being treats as escape characters
        read_datafile_str += (
            f"while IFS={self.separator} read -r "
            f"{' '.join(self.var(i) for i in range(ndata))}\n"
        )
        read_datafile_str += "do\n"
        for i in range(ndata):
            read_datafile_str += f"    {self.arr(i)}+=(${self.var(i)})\n"
        read_datafile_str += f"done < ${self.datafile_var}\n"

        return f"{datafile_str}\n{read_datafile_str}"

    def setup_datafile(
        self, datafile: Path, data: List[List[str]]
    ) -> Tuple[List[str], str]:
        """ Calls write_datafile which writes the datafile to disk (if it is not locked). Then it reads 
   
        :param datafile: Path object that points to a datafile location (which is going to be written now by write_datafile)
        :param data: A list of lists. Each inner list contains strings which are the names of the inputs and output files.
        """
        self.write_datafile(datafile, data)
        datafile_str = self.read_datafile_str(datafile, data)
        datafile_variables = [self.array_index(i) for i in range(len(data[0]))]
        set_uid()
        return datafile_variables, datafile_str

    def write(self):
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
            if njobs > 1:
                f.write(
                    f"#{BATCH_SYSTEM.OptionCmd} {BATCH_SYSTEM.array_job(njobs)}\n"
                )
            else:
                f.write(f"{BATCH_SYSTEM.TaskID}=1\n")

            # if job or array job is going to use more than 1 cores, then we need extra things to write.
            if self.ncores > 1:
                f.write(f"export OMP_NUM_THREADS={self.ncores}\n")
                f.write(f"export OMP_PROC_BIND=true\n")  # give physical cores

            # load any modules required for the job
            for module in self.modules:
                f.write(f"module load {module}\n")

            for command_group in self.grouped_commands:
                command_variables = []
                if command_group.data: # Gaussian, Ferebus, AIMALL jobs need access to datafiles
                    datafile = GLOBALS.FILE_STRUCTURE["datafiles"] / Path(
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
                    f.write(f"{datafile_str}\n")  # write the array job parts to the submission script
                f.write(f"{command_group.repr(command_variables)}\n")  # see class GaussianCommand for example

    def submit(self, hold: Optional[JobID] = None) -> Optional[JobID]:
        from ichor.globals import GLOBALS

        if not GLOBALS.SUBMITTED:
            return BATCH_SYSTEM.submit_script(self.path, hold)

    # matt_todo: Is the SubmissionScript class used as a context manager somewhere?
    def __enter__(self):
        return self

    # matt_todo: some of the arguments are not used inside the __exit__ method
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write()
