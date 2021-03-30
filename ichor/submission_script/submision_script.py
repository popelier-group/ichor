from ichor.submission_script.command_line import CommandLine
from ichor.files import File
from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.batch_system import BATCH_SYSTEM


class SubmissionScript(File):
    def __init__(self, path):
        super().__init__(path)
        self.commands = []

    @classproperty
    def filetype(self) -> str:
        return ".sh"

    def add_command(self, command):
        self.commands += [command]

    # abstract class, not needed here
    def _read_file(self) -> None:
        pass

    def write_datafile(self, data):
        pass

    @property
    def ncores(self) -> int:
        return max(command.ncores for command in self.commands)

    @property
    def default_options(self):
        return [
            f"{BATCH_SYSTEM.parallel_environment(self.ncores)}",
        ]

    @property
    def options(self):
        return list(set(option for option in self) + self.default_options)

    def write(self):
        mkdir(self.path.parent)

        with open(self.path, "w") as f:
            f.write("#!/bin/bash -l")


