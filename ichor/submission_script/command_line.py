from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

from ichor.batch_system import BATCH_SYSTEM
from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.globals import GLOBALS
from ichor.modules import Modules


class CommandLine(ABC):
    @classproperty
    @abstractmethod
    def command(self) -> str:
        pass

    @classproperty
    def ncores(self) -> int:
        return 1

    @classproperty
    def data(self) -> Tuple[str]:
        return ()

    @classproperty
    def modules(self) -> Modules:
        return Modules()

    @classproperty
    def arguments(self) -> List[str]:
        return []

    @classproperty
    def options(self) -> List[str]:
        return []

    @classmethod
    def arr(cls, n):
        return f"arr{n + 1}"

    @classmethod
    def var(cls, n):
        return f"var{n + 1}"

    @classmethod
    def batch_index(cls, n):
        return f"${{{cls.arr(n)}[{BATCH_SYSTEM.TaskID}-1]}}"

    @abstractmethod
    def repr(self) -> str:
        pass

    @classmethod
    def separator(cls) -> str:
        return ","

    @classmethod
    def datafile_var(cls) -> str:
        return "ICHOR_DATFILE"

    def write_datafile(self, datafile: Path) -> None:
        mkdir(datafile.parent)
        with open(datafile, "w") as f:
            for data in self.data:
                f.write(self.separator.join(map(str, *data)))

    def __repr__(self) -> str:
        str_rep = ""

        if self.data:
            datafile = GLOBALS.FILE_STRUCTURE["datafiles"] / Path(
                str(GLOBALS.UID)
            )
            self.write_datafile(datafile)
            datafile_str = f"{self.datafile_var}={datafile.absolute()}"

            read_datafile_str = ""
            for i in range(len(self.data)):
                read_datafile_str += f"{self.arr(i)}=()\n"
            read_datafile_str += f"while IFS={self.separator} read -r {' '.join(self.var(i) for i in range(len(self.data)))}\n"
            read_datafile_str += "do\n"
            for i in range(len(self.data)):
                read_datafile_str += f"    {self.arr(i)}+=(${self.var(i)})\n"
            read_datafile_str += f"done < {self.datafile_var}\n"

            str_rep += f"{datafile_str}\n{read_datafile_str}\n"

        str_rep += f"{self.repr()}"

        return str_rep
