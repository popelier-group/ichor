import os
import shutil
import sys
from contextlib import contextmanager
from functools import wraps
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Union

from ichor.typing import F


def convert_to_path(func: F) -> F:
    """ Used as a decorator which converts any function inputs which have type annotation `Path` to a `Path` object."""
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
    """Makes a directory.
    
    :param path: Where to make the directory
    :param empty: Whether to ignore FileExistsError exceptions. Set to False to ignore exceptions.
    :param force: When set to True (default), do not make the directory if an OSError occurs
    """
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
    """ Move the object from src to dst."""
    src.replace(dst)


@convert_to_path
def cp(src: Path, dst: Path, *args, **kwargs) -> None:
    """ See copyfile function below"""
    if src.is_file():
        copyfile(src, dst, *args, **kwargs)
    elif src.is_dir():
        copytree(src, dst, *args, **kwargs)


@convert_to_path
def copyfile(src: Path, dst: Path) -> None:
    """ Copy contents and metadata (such as date created, etc.) from src to dst.
    
    :param src: The source directory where the file/directory are currently
    :param dst: The destination directory where the file/directory are to be copied to
    """
    shutil.copy2(src, dst)


@convert_to_path
def copytree(src: Path, dst: Path, symlinks=False, ignore=None):
    """ Copy a whole tree (a folder and all of its inside contents such as subdirectories, sub-subdirectories, files, etc.)

    :param src: The source directory where the tree is currently
    :param dst: The destination directory where the tree is to be copied to
    :param symlinks: Whether or not to keep symlinks or copy the files corresponding to the symlinks (default is False, so copies the files directly)
    :param ignore: A callable which indicates which files should not be copied over.
    """
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
    """ Move a whole tree (a folder and all of its inside contents such as subdirectories, sub-subdirectories, files, etc.) or a file to a new location.

    :param src: The current location of directory of file
    :param dst: The location where the directory or file should be moved to
    """
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
    """
    Remove a file or directory and all of its contents.

    :param path: Relative or absolute path to the file/directory to be removed."""
    if path.exists():
        if path.is_file() or path.is_symlink():
            path.unlink()  # remove the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove dir and all contains
        else:
            raise ValueError(f"file {path} is not a file or dir.")


@contextmanager
def pushd(new_dir: Path, update_cwd: bool = False):
    """
    Works like the UNIX `pushd` commmand whereby it changes the current directory and stores the previous directory on the stack
    By exiting the context manager, the equivalent of `popd` is called and the location is reverted to the previous e.g.

    ```python
    # currently in /home
    with pushd('usr/bin'):
        # now in /home/usr/bin
        ...
        with pushd('/foo/bar'):
            # now in /foo/bar
            ...
        # now in /home/usr/bin
    # now back in /home
    ```

    Is good to use to temporarily change the current working directory as it is easy to return to the original location
    """
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
def get_files_of_type(
    filetype: Union[str, List[str]], directory: Path = Path.cwd()
) -> List[Path]:
    """ Returns a list of all files that end in a certain file extension/suffix (such as .txt).
    
    :param filetype: A string or list of strings corresponding to the suffixes that files should have
    :param directory: The directory where to do the searching for particular files.
    """
    if isinstance(filetype, str):
        filetype = [filetype]
    for i, ft in enumerate(filetype):
        if not ft.startswith("."):
            filetype[i] = "." + ft
    return [
        f for f in directory.iterdir() if f.is_file() and f.suffix in filetype
    ]
