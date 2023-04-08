from ichor.core.common.types import FileTree, FileType


class FileStructure(FileTree):
    """A class which manages all the files/directories that ICHOR needs
    in order to function. It makes it easier to find
    the full paths of files and directories (which could be subdirectories).
    This class is used to make a tree
    of all the directories/files. Then the full path of a directory can be obtained by doing:

    `self.ichor.hpc.global_variables.FILE_STRUCTURE["scripts"]` to get the SCRIPTS directory path.

    Because a `Path` object is returned by the above code (see the `FileNode` class),
    it makes it possible to write code like

    `if self.ichor.hpc.global_variables.FILE_STRUCTURE["scripts"].exists():`

    where the `exists()` method can be called because `self.ichor.hpc.global_variables.FILE_STRUCTURE["scripts"]`
    is a `Path` object (see pathlib library).
    """

    def __init__(self):
        super(FileStructure, self).__init__()

        # name = of the directory
        # _id = how can be internally referenced to by ichor.hpc.global_variables.FILE_STRUCTURE["internal_reference"]
        # parent = if parent is set, then make it a subdirectory of parent directory
        # description = description of directory

        self.add(
            ".DATA",
            "data",
            type_=FileType.Directory,
            description="""Directory that contains important information for jobs submitted to
            compute nodes. Submission scripts as well as job outputs among other things are stored here.""",
        )

        self.add(
            "SCRIPTS",
            "scripts",
            parent="data",
            type_=FileType.Directory,
            description="""Stores submission scripts which are used to submit
            jobs to compute nodes. Submission scripts are shell (.sh) files such as GAUSSIAN.sh and AIMALL.sh.""",
        )

        self.add(
            "OUTPUTS",
            "outputs",
            parent="scripts",
            type_=FileType.Directory,
            description="""This directory contains the standard output (stdout) that the job
            produces. Things like print statements which are written to standard
            output are going to be written here (if ran from a compute node).
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
            have information for paths to inputs and outputs of a calculation submitted
            to the computer cluster. These datafiles are used to give
                the paths to input/output files to jobs without hard-coding
                the inputs/outputs in the job script itself.""",
        )
        self.add(
            "CP2K",
            "cp2k",
            type_=FileType.Directory,
            description="""Contains files relating to the molecular dynamics package CP2K.""",
        )
        # todo: a better description for these two is needed
        self.add(
            "DLPOLY",
            "dlpoly",
            type_=FileType.Directory,
            description="""Directory with files relating to DLPOLY simulations.""",
        )
        self.add("GJF", "dlpoly_gjf", parent="dlpoly", type_=FileType.Directory)
        self.add("AMBER", "amber", type_=FileType.Directory)

        self.add(
            "machine",
            "machine",
            parent="data",
            type_=FileType.File,
            description="""A file containg the name of the comuter cluster
            we are working on (csf3, ffluxlab, etc.)""",
        )
