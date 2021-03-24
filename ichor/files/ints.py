from ichor.files.directory import Directory
from ichor.files.int import INT
from ichor.common.functools import buildermethod, classproperty
import re


class INTs(Directory, dict):
    def __init__(self, path):
        Directory.__init__(self, path)
        self.parse()

    def parse(self) -> None:
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f)

    @classproperty
    def dirpattern(self) -> re.Pattern:
        return re.compile(r".+_atomicfiles")

    @buildermethod
    def read(self):
        for atom, int_file in self.items():
            int_file.read()
