from pathlib import Path
from typing import Optional

from ichor.common.io import pushd
from ichor.tab_completer import PathCompleter


def get_path(startdir: Path = Path.cwd(), prompt="Enter Path: ") -> Path:
    with PathCompleter():
        with pushd(startdir):
            while True:
                p = Path(input(prompt))
                if not p.exists():
                    print(f"Error: Path {p} doesn't exist")
                else:
                    return p


def get_dir(startdir: Path = Path.cwd()) -> Path:
    while True:
        p = get_path(startdir=startdir, prompt="Enter Directory: ")
        if not p.is_dir():
            print(f"Error: {p} is not a directory")
        else:
            return p


def get_file(
    startdir: Path = Path.cwd(), filetype: Optional[str] = None
) -> Path:
    while True:
        ft = " " if filetype is None else f" {filetype} "
        p = get_path(startdir=startdir, prompt=f"Enter{ft}File: ")
        if not p.is_file():
            print(f"Error: {p} is not a file")
        elif filetype and p.suffix != filetype:
            print(
                f"Error: Filetype of {p} ({p.suffix}) is not of type {filetype}"
            )
        else:
            return p
