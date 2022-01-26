import os
import shutil
import stat
import sys
import time
from contextlib import contextmanager
from functools import wraps
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Optional, Union

from ichor.itypes import F


def convert_to_path(func: F) -> F:
    """Used as a decorator which converts any function inputs which have type annotation `Path` to a `Path` object."""

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
def mkdir(path: Path, empty: bool = False, fail_ok: bool = False) -> None:
    """Makes a directory.

    :param path: Where to make the directory
    :param empty: Whether to ignore FileExistsError exceptions. Set to False to ignore exceptions.
    :param fail_ok: When set to False (default), raise OSError if cannot make directory
    """
    if path.is_dir() and empty:
        try:
            shutil.rmtree(path)
        except OSError as err:
            if not fail_ok:
                raise err
    path.mkdir(parents=True, exist_ok=not empty)


@convert_to_path
def move(src: Path, dst: Path) -> None:
    """Move the object from src to dst."""
    src.replace(dst)


@convert_to_path
def cp(src: Path, dst: Path, *args, **kwargs) -> None:
    """See copyfile function below"""
    if src.is_file():
        copyfile(src, dst, *args, **kwargs)
    elif src.is_dir():
        copytree(src, dst, *args, **kwargs)


@convert_to_path
def copyfile(src: Path, dst: Path) -> None:
    """Copy contents and metadata (such as date created, etc.) from src to dst.

    :param src: The source directory where the file/directory are currently
    :param dst: The destination directory where the file/directory are to be copied to
    """
    shutil.copy2(src, dst)


@convert_to_path
def copytree(src: Path, dst: Path, symlinks=False, ignore=None):
    """Copy a whole tree (a folder and all of its inside contents such as subdirectories, sub-subdirectories, files, etc.)

    :param src: The source directory where the tree is currently
    :param dst: The destination directory where the tree is to be copied to
    :param symlinks: Whether or not to keep symlinks or copy the files corresponding to the symlinks (default is False, so copies the files directly)
    :param ignore: A callable which indicates which files should not be copied over.
    """
    for item in src.iterdir():
        s = item
        d = dst / item.name
        if s.is_dir():
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


@convert_to_path
def recursive_move(src: Path, dst: Path) -> None:
    """Move a whole tree (a folder and all of its inside contents such as subdirectories, sub-subdirectories, files, etc.) or a file to a new location.

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


@convert_to_path
def remove_with_suffix(
    suffix: str, path_to_search: Path = Path().cwd(), recursive: bool = False
) -> None:
    """
    Remove all files with given suffix 'suffix'

    :param suffix: suffix to search and remove
    :param path_to_search: path to search for files with suffix, defaults to cwd
    :param recursive: boolean to search recursively in subdirectories for files with suffix
    """
    for f in path_to_search.iterdir():
        if f.suffix == suffix:
            remove(f)
        if f.is_dir() and recursive:
            remove_with_suffix(f, path=f, recursive=recursive)


@contextmanager
@convert_to_path
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
    filetype: Union[str, List[str]],
    directory: Path = Path.cwd(),
    recursive: bool = False,
    sort: Optional[F] = None,
) -> List[Path]:
    """Returns a list of all files that end in a certain file extension/suffix (such as .txt).

    :param filetype: A string or list of strings corresponding to the suffixes that files should have
    :param directory: The directory where to do the searching for particular files.
    :param recursive: Boolean flag to recursively search subdirectories for files
    :param sort: Optional function to sort files
    """
    if isinstance(filetype, str):
        filetype = [filetype]
    for i, ft in enumerate(filetype):
        if not ft.startswith("."):
            filetype[i] = "." + ft
    files = []
    for f in directory.iterdir():
        if f.is_file() and f.suffix in filetype:
            files.append(f)
        elif f.is_dir() and recursive:
            files.extend(get_files_of_type(filetype, f, recursive=recursive))
    if sort is not None:
        files = sort(files)
    return files


@convert_to_path
def tail(path: Path, lines: int = 20) -> str:
    """Works in the same way as the unix `tail` command giving the last n lines of a file

    :param path: the path of the file to read last m lines of
    :param lines: specifies how many lines from the bottom of the file to return
    :return: last n lines of file as string
    """
    with open(path, "rb") as f:
        total_lines_wanted = lines

        BLOCK_SIZE = 1024
        f.seek(0, 2)
        block_end_byte = f.tell()
        lines_to_go = total_lines_wanted
        block_number = -1
        blocks = []
        while lines_to_go > 0 and block_end_byte > 0:
            if block_end_byte - BLOCK_SIZE > 0:
                f.seek(block_number * BLOCK_SIZE, 2)
                blocks.append(f.read(BLOCK_SIZE))
            else:
                f.seek(0, 0)
                blocks.append(f.read(block_end_byte))
            lines_found = blocks[-1].count(b"\n")
            lines_to_go -= lines_found
            block_end_byte -= BLOCK_SIZE
            block_number -= 1
        all_read_text = b"".join(reversed(blocks))
        return b"\n".join(
            all_read_text.splitlines()[-total_lines_wanted:]
        ).decode("utf-8")


@convert_to_path
def last_line(path: Path) -> str:
    """Alias for `tail` for getting the last line of a file

    :param path: the path of the file to read last line of
    :return: last line of file as string
    """
    return tail(path, lines=1)


@convert_to_path
def relpath(path: Path, start: Path) -> Path:
    """
    Returns relative path of 'path' from 'start'

    :param path: Path to return relative path of
    :param start: Path to return relative path from
    :return: relative path of 'path; from 'start'
    """
    return Path(os.path.relpath(path, start))


@convert_to_path
def cat(outfile: Path, infiles: List[Path]) -> None:
    """
    Mimics unix cat command by concatenating all infiles to outfile
    :param outfile: path to concatenate infiles to
    :param infiles: list of one or more paths to concatenatr to outfile
    :return: none
    """
    with open(outfile, "ab") as outf:
        for infile in infiles:
            with open(infile, "rb") as inf:
                shutil.copyfileobj(inf, outf)


@convert_to_path
def ln(f: Path, link: Path, force: bool = True):
    """
    Creates symlink between f and link
    :param f: file to link to
    :param link: link to create
    :param force: if the path exists then unlink first
    """
    if link.exists() and link.is_dir() and f.is_file():
        link = link / f.name
    if link.exists() and force:
        link.unlink()
    link.symlink_to(f)


@convert_to_path
def last_modified(f: Path) -> str:
    fstat = os.stat(f)
    return time.ctime(fstat[stat.ST_MTIME])
