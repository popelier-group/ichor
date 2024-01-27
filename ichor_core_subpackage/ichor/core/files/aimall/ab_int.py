from pathlib import Path
from typing import Dict, Union

from ichor.core.common.functools import classproperty
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasData


class AbInt(HasData, ReadFile):
    def __init__(self, path: Union[str, Path]):
        ReadFile.__init__(self, path)
        HasData.__init__(self)

        self.a: str = FileContents
        self.b: str = FileContents
        self.iqa_diatomic_contributions: Dict[str, float] = FileContents
        self.total_time: int = FileContents

    @property
    def raw_data(self) -> dict:
        return {
            "a": self.a,
            "b": self.b,
            "iqa_diatomic_contributions": self.iqa_diatomic_contributions,
            "total_time": self.total_time,
        }

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.suffix == cls.filetype and "_" in path.name

    @classproperty
    def filetype(self) -> str:
        return ".int"

    @property
    def e_inter(self):
        return self.iqa_diatomic_contributions["E_IQA_Inter"]

    def _read_file(self):
        self.a = ""
        self.b = ""
        self.iqa_diatomic_contributions = {}
        self.total_time = 0

        with open(self.path, "r") as f:
            line = next(f)
            while "IQA Atomic and Diatomic Contributions" not in line:
                line = next(f)

            next(f)  # ---------
            self.a = next(f).split()[-1]
            self.b = next(f).split()[-1]

            diatomic_contributions = {}
            line = next(f)
            while "=" in line:
                record = line.split()
                key = record[0].split("(")[0]
                value = float(record[2])
                if key in diatomic_contributions.keys():
                    diatomic_contributions[key] = (
                        diatomic_contributions[key] + value
                    ) / 2
                else:
                    diatomic_contributions[key] = value
                line = next(f)

            self.iqa_diatomic_contributions = diatomic_contributions

            while "Total time" not in line:
                line = next(f)

            self.total_time = int(line.split()[-2])
