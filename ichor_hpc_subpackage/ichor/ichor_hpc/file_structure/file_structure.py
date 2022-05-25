from ichor.ichor_lib.common.types import FileTree, FileType


class FileStructure(FileTree):
    """A class which manages all the files/directories that ICHOR needs in order to function. It makes it easier to find
    the full paths of files and directories (which could be subdirectories). ichor.ichor_hpc.globals uses this class to make a tree
    of all the directories/files. Then the full path of a directory can be obtained by doing:

    `self.FILE_STRUCTURE["training_set"]` to get the TRAINING_SET directory path.

    Because a `Path` object is returned by the above code (see the `FileNode` class), it makes it possible to write code like

    `if self.FILE_STRUCTURE["training_set"].exists():`

    where the `exists()` method can be called because `self.FILE_STRUCTURE["training_set"]` is a `Path` object (see pathlib library).
    """

    def __init__(self):
        super(FileStructure, self).__init__()

        # name of the directory, how the directory can be internally referenced to by FILE_STRUCTURE["internal_reference"]
        # if parent is set, then make it a subdirectory of parent directory
        self.add(
            "TRAINING_SET",
            "training_set",
            type_=FileType.Directory,
            description="""Directory for points used in GP training. The number of 
            points in this directory grows as more points are being added from the sample pool to here (with  adaptive/random sampling).""",
        )
        self.add(
            "SAMPLE_POOL",
            "sample_pool",
            type_=FileType.Directory,
            description="""Stores all other points not used for training or validation currently.
            This is the directory from which points are selected via adaptive sampling.""",
        )
        self.add(
            "VALIDATION_SET",
            "validation_set",
            type_=FileType.Directory,
            description="""Stores all points used for model validation. These points
            should NOT be present in the sample pool or training set.""",
        )
        self.add(
            "FEREBUS",
            "ferebus",
            type_=FileType.Directory,
            description="""Directory used to store ferebus-related information""",
        )
        self.add(
            "MODELS",
            "models",
            parent="ferebus",
            type_=FileType.Directory,
            description="""Directory used to store the newest models made by
            FEREBUS. These models are then moved over to MODEL_LOG directory.""",
        )

        # TODO: have not seen this MODELS directory? When are models remade?
        self.add("MODELS", "remake-models", type_=FileType.Directory)

        self.add(
            "MODEL_LOG",
            "model_log",
            type_=FileType.Directory,
            description="""Directory that holds all models that are made in an
            adaptive sampling run. As the number of training points grows, newer models are made with the updated training data and new
                model files are written out to this directory.""",
        )
        self.add(
            "COLLATED",
            "model_log_collated",
            parent="model_log",
            type_=FileType.Directory,
            description="""Directory containing either bottom-up or top-down collated models (or both) to group the 
            model files from model_log into models that can easily be used for system level analysis""",
        )
        self.add(
            "BOTTOM_UP",
            "model_log_collated_bottom_up",
            parent="model_log_collated",
            type_=FileType.Directory,
            description="""Directory containing bottom up collated models for system level analysis""",
        )
        self.add(
            "TOP_DOWN",
            "model_log_collated_top_down",
            parent="model_log_collated",
            type_=FileType.Directory,
            description="""Directory containing top down collated models for system level analysis""",
        )
        self.add(
            "SCRUBBED_POINTS",
            "scrubbed_points",
            type_=FileType.Directory,
            description="""Directory for points which have errorred out for
            some reason during the Gaussian or AIMALL calculations. If no .wfn file is produced, AIMALL fails to run, or the integration error of AIMALL is high\
                then we do not want to use the point in training, so it is moved to this directory.""",
        )
        self.add(
            "GAUSSIAN_SCRUBBED_POINTS",
            "gaussian_scrubbed_points",
            parent="scrubbed_points",
            type_=FileType.Directory,
            description="""Contains all Gaussian scrubbed points.""",
        )
        self.add(
            "AIMALL_SCRUBBED_POINTS",
            "aimall_scrubbed_points",
            parent="scrubbed_points",
            type_=FileType.Directory,
            description="""Contains all AIMALL scrubbed points.""",
        )

        self.add(
            ".DATA",
            "data",
            type_=FileType.Directory,
            description="""Directory that contains important information for jobs submitted to
            compute nodes. Submission scripts as well as job outputs among other things are stored here.""",
        )

        self.add(
            "ALF_REFERENCE_FILE",
            "alf_reference_file",
            parent="data",
            type_=FileType.File,
            description="""A reference file which contains the atomic local frame information for every atom in the system.

            Example file.
            O1,H2,H3 [[0,1,2], [1,0,2], [2,0,1]]
            O1,H2,H3,O4,H5,H6 [[0,1,2], [1,0,2], [2,0,1], [3,4,5], [4,3,5], [5,3,4]]

            Note that the file is 0 indexed (makes it easier to read)
            """
        )

        self.add(
            "SCRIPTS",
            "scripts",
            parent="data",
            type_=FileType.Directory,
            description="""Stores submission scripts which are used to submit
            jobs to compute nodes. Submission scripts are shell (.sh) files such as GAUSSIAN.sh and AIMALL.sh.""",
        )

        # TODO: not sure when temp is used
        self.add("TMP", "tmp", parent="scripts", type_=FileType.Directory)

        self.add(
            "OUTPUTS",
            "outputs",
            parent="scripts",
            type_=FileType.Directory,
            description="""This directory contains the standard output (stdout) that the job
            produces. Things like print statements which are written to standard output are going to be written here (if ran from a compute node).
                These files have the '.o' extension.""",
        )
        self.add(
            "ERRORS",
            "errors",
            parent="scripts",
            type_=FileType.Directory,
            description="""Contains standard error (stderr) which a job script/program has
            produced. These files have the '.e' extension""",
        )

        # TODO: This is for a geometry optimization correct? But is the optimization ran in this directory?
        self.add(
            "OPT",
            "opt",
            type_=FileType.Directory,
            description="""Contains a gaussian""",
        )

        self.add(
            "CP2K",
            "cp2k",
            type_=FileType.Directory,
            description="""Contains files relating to the molecular dynamics package CP2K.""",
        )

        # TODO: Is this when each model is created per-property instead of per-atom?. What
        self.add("PROPERTIES", "properties", type_=FileType.Directory)

        self.add("ATOMS", "atoms", type_=FileType.Directory)
        self.add(
            "TYCHE",
            "tyche",
            type_=FileType.Directory,
            description="""Contains files relating to TYCHE, which is a program that
            distorts a molecule by its normal modes to produce a sample pool. Currently CP2K is used to produce sample pool becaues it 
                is a full MD simulation package, so a much wider varierty of geometries are generated using it.""",
        )
        self.add(
            "GAUSSIAN",
            "tyche_g09",
            parent="tyche",
            type_=FileType.Directory,
            description="""Directory containing files from Gaussian, which
            TYCHE needs to have in order to distort a molecule by normal modes.""",
        )

        # todo: a better description for these two is needed
        self.add(
            "DLPOLY",
            "dlpoly",
            type_=FileType.Directory,
            description="""Directory with files relating to DLPOLY simulations.""",
        )
        self.add(
            "GJF", "dlpoly_gjf", parent="dlpoly", type_=FileType.Directory
        )
        self.add("AMBER", "amber", type_=FileType.Directory)

        self.add(
            "PROGRAMS",
            "programs",
            type_=FileType.Directory,
            description="""Directory containing compiled program executables such as FEREBUS.""",
        )

        # todo: pretty sure the machine is a file instead of directory, so corrected this.
        self.add(
            "machine",
            "machine",
            parent="data",
            type_=FileType.File,
            description="""A file containg the name of the comuter cluster
            we are working on (csf3, ffluxlab, etc.)""",
        )

        self.add(
            "JOBS",
            "jobs",
            parent="data",
            type_=FileType.Directory,
            description="""Directory containing information about jobs submitted to the
            queueing system.""",
        )
        self.add(
            "jid",
            "jid",
            parent="jobs",
            type_=FileType.File,
            description="""A file containing job IDs of jobs submitted to the queueing system.""",
        )
        self.add(
            "DATAFILES",
            "datafiles",
            parent="jobs",
            type_=FileType.Directory,
            description="""A directory containing datafiles, which
            have information for paths to inputs and outputs of a calculation submitted to the computer cluster. These datafiles are used to give
                the paths to input/output files to jobs without hard-coding the inputs/outputs in the job script itself.""",
        )

        # todo: not sure what this is for
        self.add(
            "ACTIVE_LEARNING",
            "active_learning",
            parent="data",
            type_=FileType.Directory,
        )
        self.add(
            "counter",
            "counter",
            parent="active_learning",
            type_=FileType.File,
            description="""File that keeps track of the iteration of the
            active learning.""",
        )
        self.add(
            "stop",
            "stop",
            parent="active_learning",
            type_=FileType.File,
            description="""File that indicates whether the active learning should stop iterating.""",
        )

        self.add(
            "alpha", "alpha", parent="active_learning", type_=FileType.File
        )
        self.add(
            "cv_errors",
            "cv_errors",
            parent="active_learning",
            type_=FileType.File,
        )

        self.add(
            "child_processes",
            "child_processes",
            parent="active_learning",
            type_=FileType.File,
        )

        self.add(
            "DAEMON",
            "daemon",
            parent="data",
            type_=FileType.Directory,
        )

        # todo: not sure what goes into these per-property folders exactly
        self.add(
            "PROPERTIES",
            "properties_daemon",
            parent="daemon",
            type_=FileType.Directory,
        )
        self.add(
            "properties.pid",
            "properties_pid",
            parent="properties_daemon",
            type_=FileType.File,
        )
        self.add(
            "properties.out",
            "properties_stdout",
            parent="properties_daemon",
            type_=FileType.File,
        )
        self.add(
            "properties.err",
            "properties_stderr",
            parent="properties_daemon",
            type_=FileType.File,
        )
        self.add("pid", "pids", parent="data", type_=FileType.File)

        self.add(
            "ATOMS",
            "atoms_daemon",
            parent="daemon",
            type_=FileType.Directory,
        )
        self.add(
            "atoms.pid",
            "atoms_pid",
            parent="atoms_daemon",
            type_=FileType.File,
        )
        self.add(
            "atoms.out",
            "atoms_stdout",
            parent="atoms_daemon",
            type_=FileType.File,
        )
        self.add(
            "atoms.err",
            "atoms_stderr",
            parent="atoms_daemon",
            type_=FileType.File,
        )

        self.add(
            "RERUN",
            "rerun_daemon",
            parent="daemon",
            type_=FileType.Directory,
        )
        self.add(
            "rerun.pid",
            "rerun_pid",
            parent="rerun_daemon",
            type_=FileType.File,
        )
        self.add(
            "rerun.out",
            "rerun_stdout",
            parent="rerun_daemon",
            type_=FileType.File,
        )
        self.add(
            "rerun.err",
            "rerun_stderr",
            parent="rerun_daemon",
            type_=FileType.File,
        )

        self.add(
            "FILES_REMOVED",
            "file_remover_daemon",
            parent="daemon",
            type_=FileType.Directory,
        )
        self.add(
            "file_remover.pid",
            "file_remover_pid",
            parent="file_remover_daemon",
            type_=FileType.File,
        )
        self.add(
            "file_remover.out",
            "file_remover_stdout",
            parent="file_remover_daemon",
            type_=FileType.File,
        )
        self.add(
            "file_remover.err",
            "file_remover_stderr",
            parent="file_remover_daemon",
            type_=FileType.File,
        )
