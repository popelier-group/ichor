from ichor.menu import Menu
from pathlib import Path
from typing import Optional, List
from ichor.file_structure import FILE_STRUCTURE
from ichor.common.io import get_files_of_type
from ichor.analysis.get_path import get_file


_input_file: Optional[Path] = None
_input_filetypes: Optional[List[str]] = None


def get_first_file(directory: Path, filetypes: List[str], recursive: bool = False) -> Optional[Path]:
    if directory.exists():
        for ft in filetypes:
            files = get_files_of_type(ft, directory, recursive=recursive)
            if len(files) > 0:
                return files[0]

    return None


def get_default_files(filetypes: List[str]) -> List[Path]:
    vs_file = get_first_file(FILE_STRUCTURE["validation_set"], filetypes)
    sp_file = get_first_file(FILE_STRUCTURE["sample_pool"], filetypes)
    files = []
    if vs_file is not None:
        files.append(vs_file)
    if sp_file is not None:
        files.append(sp_file)
    return files


def get_files_in_cwd(filetypes: List[str]) -> List[Path]:
    return get_files_of_type(filetypes, Path.cwd())


def _set_input(input_file: Path):
    global _input_file
    _input_file = input_file


def _get_input_menu_refresh(menu):
    files = get_default_files(_input_filetypes)
    files += get_files_in_cwd(_input_filetypes)
    menu.clear_options()
    for i, f in enumerate(files):
        menu.add_option(f"{i+1}", f"{f}", _set_input, kwargs={"input_file": f})
    menu.add_space()
    menu.add_option(f"c", f"Custom Input", get_file, kwargs={"filetype": _input_filetypes})
    menu.add_space()
    menu.add_message(f"Current Input File {_input_file}")
    menu.add_final_options()


def get_input_menu(current_input: Path, filetypes: Optional[List[str]] = None) -> Path:
    global _input_file
    global _input_filetypes
    _input_file = current_input
    _input_filetypes = filetypes if filetypes is not None else []
    with Menu("Choose Input Menu", refresh=_get_input_menu_refresh):
        pass
    return _input_file
