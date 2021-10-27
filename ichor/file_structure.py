from ichor.common.types import FileTree


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
        self.add("TRAINING_SET", "training_set", type_="dir")
        self.add("SAMPLE_POOL", "sample_pool", type_="dir")
        self.add("VALIDATION_SET", "validation_set", type_="dir")
        self.add("FEREBUS", "ferebus", type_="dir")
        self.add("MODELS", "models", parent="ferebus", type_="dir")
        self.add("MODELS", "remake-models", type_="dir")
        self.add("MODEL_LOG", "model_log", type_="dir")
        self.add("SCRUBBED_POINTS", "scrubbed_points", type_="dir")
        self.add(
            "GAUSSIAN_SCRUBBED_POINTS",
            "gaussian_scrubbed_points",
            parent="scrubbed_points",
            type_="dir"
        )
        self.add(
            "AIMALL_SCRUBBED_POINTS",
            "aimall_scrubbed_points",
            parent="scrubbed_points",
            type_="dir"
        )

        self.add(".DATA", "data")
        self.add("SCRIPTS", "scripts", parent="data", type_="dir")
        self.add("TEMP", "tmp_scripts", parent="scripts", type_="dir")
        self.add("OUTPUTS", "outputs", parent="scripts", type_="dir")
        self.add("ERRORS", "errors", parent="scripts", type_="dir")

        self.add("OPT", "opt")
        self.add("CP2K", "cp2k")
        self.add("PROPERTIES", "properties")
        self.add("ATOMS", "atoms")
        self.add("TYCHE", "tyche")
        self.add("GAUSSIAN", "tyche_g09", parent="tyche")
        self.add("DLPOLY", "dlpoly")
        self.add("GJF", "dlpoly_gjf", parent="dlpoly")
        self.add("AMBER", "amber")

        self.add("PROGRAMS", "programs", type_="dir")
        self.add("machine", "machine", parent="data", type_="f")
        self.add("jid", "jid", parent="jobs", type_="f")
        self.add("DATAFILES", "datafiles", parent="jobs", type_="dir")


        self.add("ACTIVE_LEARNING", "active_learning", parent="data", type_="dir")
        self.add("counter", "counter", parent="active_learning", type_="f")
        self.add(
            "child_processes", "child_processes", parent="active_learning"
        )
        self.add("PROPERTIES", "properties_daemon", parent="active_learning")
        self.add(
            "properties.pid", "properties_pid", parent="properties_daemon"
        )
        self.add(
            "properties.out", "properties_stdout", parent="properties_daemon"
        )
        self.add(
            "properties.err", "properties_stderr", parent="properties_daemon"
        )
        self.add("pid", "pids", parent="data")

        self.add("ATOMS", "atoms_daemon", parent="active_learning")
        self.add("atoms.pid", "atoms_pid", parent="atoms_daemon")
        self.add("atoms.out", "atoms_stdout", parent="atoms_daemon")
        self.add("atoms.err", "atoms_stderr", parent="atoms_daemon")

        self.add("RERUN", "rerun_daemon", parent="active_learning")
        self.add("rerun.pid", "rerun_pid", parent="rerun_daemon")
        self.add("rerun.out", "rerun_stdout", parent="rerun_daemon")
        self.add("rerun.err", "rerun_stderr", parent="rerun_daemon")

        self.add("FILES_REMOVED", "file_remover_daemon", parent="data")
        self.add(
            "file_remover.pid",
            "file_remover_pid",
            parent="file_remover_daemon",
        )
        self.add(
            "file_remover.out",
            "file_remover_stdout",
            parent="file_remover_daemon",
        )
        self.add(
            "file_remover.err",
            "file_remover_stderr",
            parent="file_remover_daemon",
        )

# this type of stuff is making sphinx execute code
FILE_STRUCTURE = FileStructure()
