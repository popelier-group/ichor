from pathlib import Path
from typing import List, Optional, Union

from ichor.common.io import pushd
from ichor.common.os import input_with_prefill
from ichor.tab_completer import PathCompleter


def get_path(
    startdir: Path = Path.cwd(), prompt="Enter Path: ", prefill: str = ""
) -> Path:
    with PathCompleter():
        with pushd(startdir):
            while True:
                p = Path(input_with_prefill(prompt, prefill))
                if not p.exists():
                    print(f"Error: Path {p} doesn't exist")
                else:
                    return p


def get_generic_path(prompt="Enter Path: ", prefill: str = "") -> Path:
    with PathCompleter():
        p = Path(input_with_prefill(prompt, prefill))
        return p


def get_dir(startdir: Path = Path.cwd()) -> Path:
    while True:
        p = get_path(startdir=startdir, prompt="Enter Directory: ")
        if not p.is_dir():
            print(f"Error: {p} is not a directory")
        else:
            return p


def get_file(
    startdir: Path = Path.cwd(),
    filetype: Optional[Union[str, List[str]]] = None,
) -> Path:
    if filetype is not None:
        if isinstance(filetype, str):
            filetype = [filetype]
    while True:
        ft = " " if filetype is None else f" {filetype} "
        p = get_path(startdir=startdir, prompt=f"Enter{ft}File: ")
        if not p.is_file():
            print(f"Error: {p} is not a file")
        elif filetype is not None and p.suffix not in filetype:
            print(
                f"Error: Filetype of {p} ({p.suffix}) is not of type {' | '.join(filetype)}"
            )
        else:
            return p
