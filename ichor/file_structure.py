from ichor.common.types import FileTree, FileType


class FileStructure(FileTree):
    """A class which manages all the files/directories that ICHOR needs in order to function. It makes it easier to find
    the full paths of files and directories (which could be subdirectories). ICHOR GLOBALS uses this class to make a tree
    of all the directories/files. Then the full path of a directory can be obtained by doing:

    `self.FILE_STRUCTURE["training_set"]` to get the TRAINING_SET directory path.

    Because a `Path` object is returned by the above code (see the `FileNode` class), it makes it possible to write code like

    `if self.FILE_STRUCTURE["training_set"].exists():`

    where the `exists()` method can be called because `self.FILE_STRUCTURE["training_set"]` is a `Path` object (see pathlib library).
    """

    def __init__(self):
        super(FileStructure, self).__init__()

        # todo: possibly add a type (either file or directory), so it is easier to distingush between directories/files here
        # e.g. self.add("counter", "counter", parent="active_learning") is a file but self.add("MODELS", "models", parent="ferebus") is a dir
        # todo: make a make method, that way we can do something like FILE_STRUCTURE["counter"].make() which will create an empty file at that location
        # and make all upper directories if they do not exist already.

        # name of the directory, how the directory can be internally referenced to by FILE_STRUCTURE["internal_reference"]
        # if parent is set, then make it a subdirectory of parent directory
        self.add("TRAINING_SET", "training_set", type_=FileType.Directory)
        self.add("SAMPLE_POOL", "sample_pool", type_=FileType.Directory)
        self.add("VALIDATION_SET", "validation_set", type_=FileType.Directory)
        self.add("FEREBUS", "ferebus", type_=FileType.Directory)
        self.add("MODELS", "models", parent="ferebus", type_=FileType.Directory)
        self.add("MODELS", "remake-models", type_=FileType.Directory)
        self.add("MODEL_LOG", "model_log", type_=FileType.Directory)
        self.add("SCRUBBED_POINTS", "scrubbed_points", type_=FileType.Directory)
        self.add(
            "GAUSSIAN_SCRUBBED_POINTS",
            "gaussian_scrubbed_points",
            parent="scrubbed_points",
            type_=FileType.Directory
        )
        self.add(
            "AIMALL_SCRUBBED_POINTS",
            "aimall_scrubbed_points",
            parent="scrubbed_points",
            type_=FileType.Directory
        )

        self.add(".DATA", "data", type_=FileType.Directory)
        self.add("SCRIPTS", "scripts", parent="data", type_=FileType.Directory)
        self.add("TEMP", "tmp_scripts", parent="scripts", type_=FileType.Directory)
        self.add("OUTPUTS", "outputs", parent="scripts", type_=FileType.Directory)
        self.add("ERRORS", "errors", parent="scripts", type_=FileType.Directory)

        self.add("OPT", "opt", type_=FileType.Directory)
        self.add("CP2K", "cp2k", type_=FileType.Directory)
        self.add("PROPERTIES", "properties", type_=FileType.Directory)
        self.add("ATOMS", "atoms", type_=FileType.Directory)
        self.add("TYCHE", "tyche", type_=FileType.Directory)
        self.add("GAUSSIAN", "tyche_g09", parent="tyche", type_=FileType.Directory)
        self.add("DLPOLY", "dlpoly", type_=FileType.Directory)
        self.add("GJF", "dlpoly_gjf", parent="dlpoly", type_=FileType.Directory)
        self.add("AMBER", "amber", type_=FileType.Directory)

        self.add("PROGRAMS", "programs", type_=FileType.Directory)
        self.add("machine", "machine", parent="data", type_=FileType.Directory)

        self.add("JOBS", "jobs", parent="data", type_=FileType.Directory)
        self.add("jid", "jid", parent="jobs", type_=FileType.File)
        self.add("DATAFILES", "datafiles", parent="jobs", type_=FileType.Directory)

        self.add("ACTIVE_LEARNING", "active_learning", parent="data", type_=FileType.Directory)
        self.add("counter", "counter", parent="active_learning", type_=FileType.File)
        self.add(
            "child_processes", "child_processes", parent="active_learning", type_=FileType.Directory
        )
        self.add("PROPERTIES", "properties_daemon", parent="active_learning", type_=FileType.Directory)
        self.add(
            "properties.pid", "properties_pid", parent="properties_daemon", type_=FileType.File
        )
        self.add(
            "properties.out", "properties_stdout", parent="properties_daemon", type_=FileType.File
        )
        self.add(
            "properties.err", "properties_stderr", parent="properties_daemon", type_=FileType.File
        )
        self.add("pid", "pids", parent="data", type_=FileType.File)

        self.add("ATOMS", "atoms_daemon", parent="active_learning", type_=FileType.Directory)
        self.add("atoms.pid", "atoms_pid", parent="atoms_daemon", type_=FileType.File)
        self.add("atoms.out", "atoms_stdout", parent="atoms_daemon", type_=FileType.File)
        self.add("atoms.err", "atoms_stderr", parent="atoms_daemon", type_=FileType.File)

        self.add("RERUN", "rerun_daemon", parent="active_learning", type_=FileType.Directory)
        self.add("rerun.pid", "rerun_pid", parent="rerun_daemon", type_=FileType.File)
        self.add("rerun.out", "rerun_stdout", parent="rerun_daemon", type_=FileType.File)
        self.add("rerun.err", "rerun_stderr", parent="rerun_daemon", type_=FileType.File)

        self.add("FILES_REMOVED", "file_remover_daemon", parent="data", type_=FileType.Directory)
        self.add(
            "file_remover.pid",
            "file_remover_pid",
            parent="file_remover_daemon",
            type_ = FileType.File,
        )
        self.add(
            "file_remover.out",
            "file_remover_stdout",
            parent="file_remover_daemon",
            type_ = FileType.File,
        )
        self.add(
            "file_remover.err",
            "file_remover_stderr",
            parent="file_remover_daemon",
            type_ = FileType.Directory,
        )


# this type of stuff is making sphinx execute code
FILE_STRUCTURE = FileStructure()
