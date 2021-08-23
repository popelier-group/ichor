from ichor.file_structure.node import FileNode
from ichor.file_structure.tree import FileTree

__all__ = ["FileStructure"]


class FileStructure(FileTree):
    def __init__(self):
        super(FileStructure, self).__init__()

        self.add("TRAINING_SET", "training_set")
        self.add("SAMPLE_POOL", "sample_pool")
        self.add("VALIDATION_SET", "validation_set")
        self.add("FEREBUS", "ferebus")
        self.add("MODELS", "models", parent="ferebus")
        self.add("MODELS", "remake-models")
        self.add("MODEL_LOG", "model_log")

        self.add("OPT", "opt")
        self.add("CP2K", "cp2k")
        self.add("PROPERTIES", "properties")
        self.add("ATOMS", "atoms")

        self.add("DLPOLY", "dlpoly")
        self.add("GJF", "dlpoly_gjf", parent="dlpoly")

        self.add(".DATA", "data")

        self.add("PROGRAMS", "programs")  # , parent="data")
        self.add("data", "data_file", parent="data")

        self.add("JOBS", "jobs", parent="data")
        self.add("jid", "jid", parent="jobs")
        self.add("DATAFILES", "datafiles", parent="jobs")

        self.add("ADAPTIVE_SAMPLING", "adaptive_sampling", parent="data")
        self.add("alpha", "alpha", parent="adaptive_sampling")
        self.add("cv_errors", "cv_errors", parent="adaptive_sampling")
        self.add("counter", "counter", parent="adaptive_sampling")

        self.add("PROPERTIES", "properties_daemon", parent="adaptive_sampling")
        self.add(
            "properties.pid", "properties_pid", parent="properties_daemon"
        )
        self.add(
            "properties.out", "properties_stdout", parent="properties_daemon"
        )
        self.add(
            "properties.err", "properties_stderr", parent="properties_daemon"
        )

        self.add("ATOMS", "atoms_daemon", parent="adaptive_sampling")
        self.add("atoms.pid", "atoms_pid", parent="atoms_daemon")
        self.add("atoms.out", "atoms_stdout", parent="atoms_daemon")
        self.add("atoms.err", "atoms_stderr", parent="atoms_daemon")

        self.add("counter", "counter", parent="adaptive_sampling")

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

        self.add("SCRIPTS", "scripts", parent="data")
        self.add("TEMP", "tmp_scripts", parent="scripts")
        self.add("OUTPUTS", "outputs", parent="scripts")
        self.add("ERRORS", "errors", parent="scripts")

    def modify(self, node_name, node_value):
        self[node_name] = FileNode(node_value, self[node_name].parent)
