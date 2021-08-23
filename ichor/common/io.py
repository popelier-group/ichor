import os
import shutil
import sys
from functools import wraps
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Union

from contextlib import contextmanager

from ichor.typing import F


def convert_to_path(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if func.__annotations__:
            args = list(args)
            annotations = func.__annotations__.items()
            for i, ((annotation, type_), arg) in enumerate(
                zip_longest(annotations, args)
            ):
                if annotation and arg:
                    if type_ is Path and not isinstance(arg, Path):
                        args[i] = Path(arg)
            for kw, arg in kwargs.items():
                if kw in func.__annotations__.keys():
                    if func.__annotations__[kw] is Path:
                        kwargs[kw] = Path(arg)
        return func(*args, **kwargs)

    return wrapper


@convert_to_path
def mkdir(path: Path, empty: bool = False, force: bool = True) -> None:
    if path.is_dir() and empty:
        try:
            shutil.rmtree(path)
        except OSError as err:
            if force:
                print(str(err))
                sys.exit(1)
    path.mkdir(parents=True, exist_ok=not empty)


@convert_to_path
def move(src: Path, dst: Path) -> None:
    src.replace(dst)


@convert_to_path
def cp(src: Path, dst: Path, *args, **kwargs) -> None:
    if src.is_file():
        copyfile(src, dst, *args, **kwargs)
    elif src.is_dir():
        copytree(src, dst, *args, **kwargs)


@convert_to_path
def copyfile(src: Path, dst: Path) -> None:
    shutil.copy2(src, dst)


@convert_to_path
def copytree(src: Path, dst: Path, symlinks=False, ignore=None):
    for item in src.iterdir():
        s = item
        d = dst / item.name
        print(s, d)
        if s.is_dir():
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


@convert_to_path
def recursive_move(src: Path, dst: Path) -> None:
    if src.isdir():
        for f in src.iterdir():
            if f.isdir() and (dst / f.name).exists():
                recursive_move(f, dst / f.name)
            else:
                move(f, dst)
    else:
        move(src, dst)


@convert_to_path
def remove(path: Path) -> None:
    """ param <path> could either be relative or absolute. """
    if path.exists():
        if path.is_file() or path.is_symlink():
            path.unlink()  # remove the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove dir and all contains
        else:
            raise ValueError(f"file {path} is not a file or dir.")


@contextmanager
def pushd(new_dir: Path, update_cwd: bool = False):
    previous_dir = os.getcwd()
    if update_cwd:
        from ichor.globals import GLOBALS
        GLOBALS.CWD = new_dir.absolute()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)
        if update_cwd:
            from ichor.globals import GLOBALS
            GLOBALS.CWD = previous_dir



@convert_to_path
def get_files_of_type(filetype: Union[str, List[str]], directory: Path = Path.cwd()) -> List[Path]:
    if isinstance(filetype, str):
        filetype = [filetype]
    for i, ft in enumerate(filetype):
        if not ft.startswith("."):
            filetype[i] = "." + ft
    return [f for f in directory.iterdir() if f.is_file() and f.suffix in filetype]


