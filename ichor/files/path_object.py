from abc import ABC
from pathlib import Path


class PathObject(ABC):
    def __init__(self, path):
        self.path = Path(path)

        if self.exists():
            from ichor.files.directory import Directory

            if (
                Directory in self.__class__.__bases__
                and not self.path.is_dir()
            ):
                raise TypeError(f"{self.path} is not a directory")

            from ichor.files.file import File

            if File in self.__class__.__bases__ and not self.path.is_file():
                raise TypeError(f"{self.path} is not a file")

    def exists(self) -> bool:
        return self.path.exists()
