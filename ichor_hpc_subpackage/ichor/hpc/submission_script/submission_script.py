from pathlib import Path
from typing import List, Optional, Tuple, Union

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.core.common.io import mkdir
from ichor.hpc.batch_system import JobID, NodeType
from ichor.hpc.submission_script.command_group import CommandGroup
from ichor.hpc.uid import get_uid


class SubmissionScript:
    """
    A class that can be used to construct submission scripts for various programs such as Gaussian and AIMALL.

    :param path: A path to a submission script (such as GAUSSIAN.sh and AIMALL.sh).
        These .sh files are submitted as jobs to CSF3/FFLUXLAB.
        These job scripts will have different contents depending on the number of cores selected,
        the number of tasks to do (if running an array job), etc.,
        so they need to be written out dynamically depending on what is going to be ran.
    :param submission_script_name: The name of the submission script
    :param ncores: Number of cores to run the job with
    :param cwd: The current working directory. If not set, defaults to Path.cwd()
    :param include_nodes: A list of node names to run the job on, defaults to None
    :param exclude_nodes: A list of node names to exclude running the job on, defaults to None
    :param max_running_tasks: Maximum number of tasks (of array job) that can run at once, defaults to -1
    :param outputs_dir_path: Path to the outputs directory. If not set, it will use the default global_variables one
    :param errors_dir_path: Path to the errors directory. If not set, it will use the default global_variables one
    :param datafile_path: Path to datafile containing information needed for job to run, defaults to None


    Example Gaussian submission script for SGE (array job):

    .. code-block:: text

        #!/bin/bash -l
        #$ -o /net/scratch2/mbdxwym4/ammonia_with_derivatives/.DATA/SCRIPTS/OUTPUTS
        #$ -pe smp.pe 2
        #$ -wd /net/scratch2/mbdxwym4/ammonia_with_derivatives
        #$ -e /net/scratch2/mbdxwym4/ammonia_with_derivatives/.DATA/SCRIPTS/ERRORS
        #$ -t 1-10000
        echo "Loading Modules | $(date)"
        module load apps/binapps/gaussian/g09d01_em64t
        export OMP_NUM_THREADS=2
        echo "Starting Job | $(date)"
        ICHOR_DATFILE=/net/scratch2/mbdxwym4/ammonia_with_derivatives/.DATA/JOBS/DATAFILES/dd644974-c430-449a-a8e1-d3540980bcb4
        arr1=()
        arr2=()
        while IFS=, read -r var1 var2
        do
            arr1+=($var1)
            arr2+=($var2)
        done < $ICHOR_DATFILE
        if [ -n ${arr1[$SGE_TASK_ID-1]} ] && [ -n ${arr2[$SGE_TASK_ID-1]} ]
        then
        export GAUSS_SCRDIR=$(dirname ${arr1[$SGE_TASK_ID-1]})
        $g09root/g09/g09 ${arr1[$SGE_TASK_ID-1]} ${arr2[$SGE_TASK_ID-1]}
        fi
        echo "Finished Job | $(date)"

    Example Gaussian submission script for SLURM (array job):

    .. code-block:: text

        #!/bin/bash -l
        #SBATCH -p multicore
        #SBATCH -n 2
        #SBATCH -e /gpfs01/scratch/mbdxwym4/glycine_paper_geometries_gaussian_with_forces/.DATA/SCRIPTS/ERRORS/%x.e%A.%a # noqa: E501
        #SBATCH -o /gpfs01/scratch/mbdxwym4/glycine_paper_geometries_gaussian_with_forces/.DATA/SCRIPTS/OUTPUTS/%x.o%A.%a # noqa: E501
        #SBATCH -D /gpfs01/scratch/mbdxwym4/glycine_paper_geometries_gaussian_with_forces
        #SBATCH -a 1-3965
        echo "Loading Modules | $(date)"
        module load gaussian/g16c01_em64t_detectcpu
        export OMP_NUM_THREADS=2
        echo "Starting Job | $(date)"
        ICHOR_DATFILE=/gpfs01/scratch/mbdxwym4/glycine_paper_geometries_gaussian_with_forces/.DATA/JOBS/DATAFILES/78a3e81e-617e-475d-809b-01501f67bfc9 # noqa: E501
        arr1=()
        arr2=()
        while IFS=, read -r var1 var2
        do
            arr1+=($var1)
            arr2+=($var2)
        done < $ICHOR_DATFILE
        if [ -n ${arr1[$SLURM_ARRAY_TASK_ID-1]} ] && [ -n ${arr2[$SLURM_ARRAY_TASK_ID-1]} ]
        then
        export GAUSS_SCRDIR=$(dirname ${arr1[$SLURM_ARRAY_TASK_ID-1]})
        $g16root/g16/g16 ${arr1[$SLURM_ARRAY_TASK_ID-1]} ${arr2[$SLURM_ARRAY_TASK_ID-1]}
        fi
        echo "Finished Job | $(date)"

    """

    # separator which is used to separate names of files in the datafiles
    # (files with random UID names) which are written by ICHOR.
    SEPARATOR = ","
    # name of the bash variable which is used to store the location of the datafile for the given job.
    DATAFILE = "ICHOR_DATFILE"

    def __init__(
        self,
        submission_script_name: Union[str, Path],
        ncores: int,
        cwd: Path = None,
        include_nodes: List[str] = None,
        exclude_nodes: List[str] = None,
        max_running_tasks: int = -1,
        outputs_dir_path: Path = None,
        errors_dir_path: Path = None,
        datafile_path: Path = None,
    ):

        self.path = Path(submission_script_name)
        self.uid = get_uid()
        self.cwd = cwd or Path.cwd()
        self.ncores = ncores
        self.include_nodes = include_nodes or []
        self.exclude_nodes = exclude_nodes or []
        self.max_running_tasks = max_running_tasks
        self._options = []
        self._commands = []  # a list of commands to be submitted to batch system

        self.outputs_dir_path = (
            outputs_dir_path or ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        )
        self.errors_dir_path = (
            errors_dir_path or ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
        )
        self.datafile_path = datafile_path or ichor.hpc.global_variables.FILE_STRUCTURE[
            "datafiles"
        ] / Path(str(self.uid))

        mkdir(self.outputs_dir_path)
        mkdir(self.errors_dir_path)

    @classproperty
    def filetype(self) -> str:
        """The extension of the submission script file. Will always be .sh (a shell script)"""
        return ".sh"

    def add_command(self, command):
        """Add a command to the list of commands."""
        self._commands.append(command)

    def add_option(self, command):
        """Add a command to the list of commands."""
        self._options.append(command)

    @property
    def grouped_commands(self) -> List[CommandGroup]:
        """
        Group commands if they need to be submitted into an array job.
        These commands will all be the same type, i.e. they will all be Gaussian jobs,
        or AIMALL jobs. Sometimes ICHOR needs to be ran after the job is complete
        (for example ICHOR needs to be ran after a FEREBUS job in order to do adaptive sampling).

        e.g. if we had a list of commands like the following:
        [Gaussian, Gaussian, Ichor, AIMAll, AIMAll]
        The commands will be grouped by type:
        [[Gaussian, Gaussian], [Ichor], [AIMAll, AIMAll]]

        The groupings are then used to allocate a task array to the batch system
        """
        # command group just allows us to get attributes of group commands
        command_group = CommandGroup(self._commands)

        if command_group.ntypes > 1:
            raise ValueError(
                "Only one type of jobs can be submitted in one submission script."
            )

        return command_group

    @property
    def default_options(self) -> List[str]:

        """Returns a list of default options to use in a submission script for a job.
        This list containing the current working directory, the output directory (where .o files are written),
        the errors directory (where .e files are written). If the number of cores is more than 1, the keyword
        needed when specifying more than 1 cores is also written to the options list. This keyword depends on
        the system on which the job is ran, as well as on the number of cores that the job needs."""

        task_array = len(self.grouped_commands) > 1

        # change current working directory to directory from which ICHOR is launched.
        # make the paths to outputs and errors absolute
        script_options = [
            ichor.hpc.global_variables.BATCH_SYSTEM.change_working_directory(self.cwd),
            ichor.hpc.global_variables.BATCH_SYSTEM.output_directory(
                self.outputs_dir_path.absolute(),
                task_array,
            ),
            ichor.hpc.global_variables.BATCH_SYSTEM.error_directory(
                self.errors_dir_path.absolute(),
                task_array,
            ),
        ]

        # if the number of cores is more than 1, have to add additional options
        pe = ichor.hpc.global_variables.BATCH_SYSTEM.parallel_environment(self.ncores)
        if pe is not None:
            script_options.append(pe)

        return script_options

    @property
    def options(self) -> List[str]:
        """Return the complete list of options (default options + other options that are specific to the job)."""
        return list(set(self._options + self.default_options))

    @property
    def modules(self) -> List[str]:
        """Returns a list of modules that need to be loaded before a job can be ran."""

        modules = []
        for command in self.grouped_commands:
            # modules depend on which machine (CSF/FFLUXLAB) we are currently on
            # also some commands might not need to load in modules
            if command.modules:
                modules += command.modules[ichor.hpc.global_variables.MACHINE]
        return list(set(modules))

    @property
    def bash_date(self) -> str:
        return "$(date)"

    def arr(cls, n):
        """Returns the keyword which is used to select array jobs.
        Since array jobs start at 1 instead of 0, 1 needs to be added
        to the array size."""
        return f"arr{n + 1}"

    def array_index(cls, n):
        """Returns the keywords used to run an array job through a program such as Gaussian.

        .. note::
            For example, this line in GAUSSIAN.sh (the submission script for Gaussian) is
            g09 ${arr1[$SGE_TASK_ID-1]} ${arr2[$SGE_TASK_ID-1]}
            The g09 is the program (however this depend on which system you are on).
            The rest is what is returned by this method.
        """
        # Note: double {{ }} is python notation for writing a curly brace in an f-string
        return f"${{{cls.arr(n)}[${ichor.hpc.global_variables.BATCH_SYSTEM.TaskID}-1]}}"

    def var(cls, n):
        return f"var{n + 1}"

    # TODO: possibly not needed anymore as scrubbing is removed, but keep
    # because it is a good check to make sure that input and outut are specified,
    def test_array_not_null(cls, n):
        """Returns a string which is used in bash to test if an array entry is not null or empty.
        We need to test this because there could be cases where there are 2000 SGE tasks for example,
        but there are only 1990 jobs (because points have been scrubbed in the previous step).

        .. note::
            the [ -n is used for the test program in bash which makes sure array entry is not null with -n

        """
        return f"[ -n {cls.array_index(n)} ]"

    def write_datafile(self, datafile: Path, data: List[List[str]]) -> None:
        """Write the datafile to disk. All datafiles are stored in
        self.datafile_path . Each line of the
        datafile contains text that corresponds to the inputs and output file names.
        These are separated by self.separator, which is a comma.

        .. note::
            For example, a datafile, which has a random name (which is set by self.uid) contains lines in the form of:
            WATER0001.gjf,WATER0001.gau
            WATER0002.gjf,WATER0002.gau
            ...
        """
        mkdir(datafile.parent)
        with open(datafile, "w") as f:
            for cmd_data in data:
                # Note: cmd_data should already be strings but we will perform a map just to be safe
                f.write(f"{SubmissionScript.SEPARATOR.join(map(str, cmd_data))}\n")

    def generate_str_for_reading_datafile(
        self, datafile: Path, data: List[List[str]]
    ) -> str:
        """Forms the strings for array jobs which are then written to the submission script to specify the number of
        tasks in the array job and things like that. Easiest to see if you
        have GAUSSIAN.sh or another submission script opened.
        """

        # number of files needed for one of the tasks in the array job
        ndata = len(data[0])

        # absolute location of datafile on disk
        datafile_str = f"{SubmissionScript.DATAFILE}={datafile.absolute()}"

        # writes out the strings which correspond to arrays containing
        # input/output file names (as read from the datafile)
        # Note: implemented as generator so that a list generation and comprehension is not required
        read_datafile_str = "".join(f"{self.arr(i)}=()\n" for i in range(ndata))

        # writes out the while loop needed to read in files names into their corresponding arrays
        # -r option prevents backslashes from being treated as escape characters
        read_datafile_str += f"while IFS={SubmissionScript.SEPARATOR} read -r {' '.join(self.var(i) for i in range(ndata))}\n"  # noqa E501
        read_datafile_str += "do\n"

        # lines which will add the things read in from the datafile to the previously made arrays
        for i in range(ndata):
            read_datafile_str += f"    {self.arr(i)}+=(${self.var(i)})\n"

        read_datafile_str += f"done < ${SubmissionScript.DATAFILE}\n"

        # checks if array entries are not empty, so that we do not get errors
        # when points are scrubbed in Gaussian and AIMALL is ran after
        # these errors do not cause calculation issues, but they are written to the ERRORS directory
        # Eg. Running 2000 Gaussians, 1996 produce .wfns, but AIMALL is set to run 2000 tasks
        # AIMALL datafile only has 1996 lines, but AIMALL tasks are set to 2000, so last 4 will fail
        # saying that there is an ambiguous redirect because the array values are empty for them
        # space is important because if[ will cause errors because [ is the test program in bash
        read_datafile_str += "if "
        read_datafile_str += " && ".join(
            [self.test_array_not_null(i) for i in range(ndata)]
        )
        # only if array entries are not empty then execute the programs
        # the \n after then is added in the `write` method
        read_datafile_str += "\nthen"

        return f"{datafile_str}\n{read_datafile_str}"

    def setup_datafile(
        self, datafile: Path, data: List[List[str]]
    ) -> Tuple[List[str], str]:
        """Calls write_datafile which writes the datafile to disk (if it is not locked). Then it reads

        :param datafile: Path object that points to a datafile location
            (which is going to be written now by write_datafile)
        :param data: A list of lists. Each inner list contains strings
            which are the names of the inputs and output files.
        """
        self.write_datafile(datafile, data)
        read_datafile_str = self.generate_str_for_reading_datafile(datafile, data)
        datafile_variables = [self.array_index(i) for i in range(len(data[0]))]
        # TODO: check if this is needed
        # set_uid()
        return datafile_variables, read_datafile_str

    def write(self):
        """Writes the submission script that is passed to the queuing system.
        The options for the job (such as directory, number of jobs, core count, etc.)
        are written at the top of the file. The commands to run (such as Gaussian, AIMALL, etc.)
        are written below the options."""

        mkdir(self.path.parent)

        if self.grouped_commands:

            njobs = len(self.grouped_commands)

            with open(self.path, "w") as f:

                f.write("#!/bin/bash -l\n")
                # write any options to be given to the batch system,
                # such as working directory, where to write outputs/errors, etc.
                for option in self.options:
                    f.write(
                        f"#{ichor.hpc.global_variables.BATCH_SYSTEM.OptionCmd} {option}\n"
                    )

                # compute nodes to include or exclude for job
                if self.include_nodes or self.exclude_nodes:
                    f.write(
                        f"#{ichor.hpc.global_variables.BATCH_SYSTEM.OptionCmd} {ichor.hpc.global_variables.BATCH_SYSTEM.node_options(self.include_nodes, self.exclude_nodes)}\n"  # noqa E501
                    )

                # if writing an array jobs, then the batch system needs to know that
                # on SGE, this is given by the #$ -t 1-{njobs}. SGE starts counting from 1 instead of 0.
                if njobs > 1:
                    f.write(
                        f"#{ichor.hpc.global_variables.BATCH_SYSTEM.OptionCmd} {ichor.hpc.global_variables.BATCH_SYSTEM.array_job(njobs)}\n"  # noqa E501
                    )
                    # this is instead of njobs > self.max_running_tasks and self.max_running_tasks > 0
                    if njobs > self.max_running_tasks > 0:
                        f.write(
                            f"#{ichor.hpc.global_variables.BATCH_SYSTEM.OptionCmd} {ichor.hpc.global_variables.BATCH_SYSTEM.max_running_tasks(self.max_running_tasks)}\n"  # noqa E501
                        )

                # load any modules required for the job
                f.write(f'echo "Loading Modules | {self.bash_date}"\n')
                for module in self.modules:
                    f.write(f"module load {module}\n")

                # if job or array job is going to use more than 1 core
                # then need to specify in options, as well as set OMP_NUM_THREADS, so program uses that amount of cores
                if self.ncores > 1:
                    f.write(f"export OMP_NUM_THREADS={self.ncores}\n")

                f.write(f'echo "Starting Job | {self.bash_date}"\n')
                # used to check if there was any command group that requires a datafile
                # Gaussian, Ferebus, AIMALL jobs need access to datafiles
                # the datafile's name is the unique id that was assigned to the submission script
                requires_datafile = self.grouped_commands.data

                # if we got to this part of the code, then we definitely need to check array entries read from datafile
                if requires_datafile:

                    # get the data that is needed for each command in a command group
                    # for example, if the command is a Gaussian command, then we
                    # need an input file (.gjf) and an output file (.gau)
                    # command_group_data is a list of lists. Each inner list has input/output files
                    command_group_data = [
                        command.data for command in self.grouped_commands
                    ]
                    # array_indices is a list of strings that will index the arrays created by datafile_str
                    # then the correct files are used in each task of the array job
                    # for example, it can be ["${arr1[$SGE_TASK_ID-1]}", "${arr2[$SGE_TASK_ID-1]}"]
                    # datafile_str is the rest of the stuff that sets up the arrays used
                    # for the array job in the submission script
                    array_indices, datafile_str = self.setup_datafile(
                        self.datafile_path, command_group_data
                    )
                    # write parts which read in the datafile
                    f.write(f"{datafile_str}\n")
                    # write parts which run the command (for example lines that run Gaussian Program)
                    f.write(f"{self.grouped_commands.repr(array_indices)}\n")
                    # close the if statement that was started when checking if arrays have non-null entries
                    # (see self.generate_str_for_reading_datafile)
                    # only write this if there was a command that required a datafile.
                    # Otherwise this will not be written
                    f.write("fi\n")

                # if no datafile is required, then can just write the command to run
                else:
                    f.write(f"{self.grouped_commands.repr()}\n")

                f.write(f'echo "Finished Job | {self.bash_date}"\n')

        else:

            ichor.hpc.global_variables.logger.info(
                f"Submission script{self.path} was not written out because there were no jobs to add to it."
            )

    def submit(self, hold: Optional[JobID] = None) -> Optional[JobID]:

        if (
            ichor.hpc.global_variables.BATCH_SYSTEM.current_node()
            is not NodeType.ComputeNode
        ):
            return ichor.hpc.global_variables.BATCH_SYSTEM.submit_script(
                self.path, hold
            )

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
        """Writes out the submission script once the `with` context manager is done.
        The exc_type, exc_val, exc_tb are needed for every __exit__ method.

        :param exception_type: If an exception has ocurred during the context, the write method will not be executed
        :param exception_value: Not used
        :param exception_traceback: Not used

        .. note::
            This does not submit the submission script, it only writes it to disk.
        """
        if exception_type is None:
            self.write()
