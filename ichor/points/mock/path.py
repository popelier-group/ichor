from pathlib import Path
from typing import Union


class MockPath(Path):
    def __init__(self, path: Union[str, Path], nfiles: int):
        super().__init__(path)
        self.nfiles = nfiles
