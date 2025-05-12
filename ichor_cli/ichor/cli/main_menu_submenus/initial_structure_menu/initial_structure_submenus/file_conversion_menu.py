from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from ase import io
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path, user_input_restricted

AVAILABLE_READ_FILE_FORMATS = [
    "abinit-gsr",
    "abinit-in",
    "abinit-out",
    "acemolecule-input",
    "acemolecule-out",
    "aims",
    "aims-output",
    "bundletrajectory",
    "castep-castep",
    "castep-cell",
    "castep-geom",
    "castep-md",
    "castep-phonon",
    "cfg",
    "cif",
    "cjson",
    "cmdft",
    "cp2k-dcd",
    "cp2k-restart",
    "crystal",
    "cube",
    "dacapo-text",
    "db",
    "dftb",
    "dlp-history",
    "dlp4",
    "dmol-arc",
    "dmol-car",
    "dmol-incoor",
    "elk",
    "eon",
    "espresso-in",
    "espresso-out",
    "extxyz",
    "gamess-us-out",
    "gamess-us-punch",
    "gaussian-in",
    "gaussian-out",
    "gen",
    "gpaw-out",
    "gpumd",
    "gpw",
    "gromacs",
    "gromos",
    "json",
    "jsv",
    "lammps-data",
    "lammps-dump-binary",
    "lammps-dump-text",
    "magres",
    "mol",
    "mustem",
    "mysql",
    "netcdftrajectory",
    "nomad-json",
    "nwchem-in",
    "nwchem-out",
    "octopus-in",
    "onetep-in",
    "onetep-out",
    "postgresql",
    "prismatic",
    "proteindatabank",
    "qbox",
    "res",
    "rmc6f",
    "sdf",
    "siesta-xv",
    "struct",
    "struct_out",
    "sys",
    "traj",
    "turbomole",
    "turbomole-gradient",
    "v-sim",
    "vasp",
    "vasp-out",
    "vasp-xdatcar",
    "vasp-xml",
    "wout",
    "xsd",
    "xsf",
    "xtd",
    "xyz",
]

AVAILABLE_WRITE_FILE_FORMATS = [
    "abinit-in",
    "aims",
    "bundletrajectory",
    "castep-cell",
    "castep-geom",
    "castep-md",
    "cfg",
    "cif",
    "crystal",
    "cube",
    "db",
    "dftb",
    "dlp4",
    "dmol-arc",
    "dmol-car",
    "dmol-incoor",
    "elk-in",
    "eon",
    "eps",
    "espresso-in",
    "extxyz",
    "findsym",
    "gamess-us-in",
    "gaussian-in",
    "gen",
    "gif",
    "gpumd",
    "gromacs",
    "gromos",
    "html",
    "json",
    "jsv",
    "lammps-data",
    "magres",
    "mp4",
    "mustem",
    "mysql",
    "netcdftrajectory",
    "nwchem-in",
    "onetep-in",
    "png",
    "postgresql",
    "pov",
    "prismatic",
    "proteindatabank",
    "py",
    "res",
    "rmc6f",
    "struct",
    "sys",
    "traj",
    "turbomole",
    "v-sim",
    "vasp",
    "vasp-xdatcar",
    "vti",
    "vtu",
    "x3d",
    "xsd",
    "xsf",
    "xtd",
    "xyz",
]

FILE_CONVERSION_MENU_DESCRIPTION = MenuDescription(
    "File Conversion Menu",
    subtitle="Use this menu to to convert between common file types.\n",
)

FILE_CONVERSION_MENU_DEFAULTS = {
    "default_output_file": "xyz",
}

# dataclass used to store values for FileConversionMenu


@dataclass
class FileConversionMenuOptions(MenuOptions):
    selected_input_file_path: Path
    selected_output_file_format: str

    def check_selected_file_path(self) -> Union[str, None]:
        """Checks whether the given file exists."""
        db_path = Path(self.selected_input_file_path)
        if not db_path.exists():
            return f"Current file path: {db_path} does not exist."


# initialize dataclass for storing information for menu
file_conversion_menu_options = FileConversionMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH,
    *FILE_CONVERSION_MENU_DEFAULTS.values(),
)


# class with static methods for each menu item that calls a function.
class FileConversionFunctions:
    @staticmethod
    def select_input_file_path():
        """Asks user to select path to input file"""

        db_path = user_input_path("Change database path: ")
        ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH = Path(
            db_path
        ).absolute()
        file_conversion_menu_options.selected_input_file_path = (
            ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH
        )

    @staticmethod
    def select_output_file_format():
        """Asks user to select the output file format eg .mol, .xyz."""

        file_conversion_menu_options.selected_output_file_format = (
            user_input_restricted(
                AVAILABLE_WRITE_FILE_FORMATS,
                "Choose an output file format: ",
                file_conversion_menu_options.selected_output_file_format,
            )
        )

    @staticmethod
    def convert_file():
        """Converts file from input to selected output format."""

        loaded_atoms = io.read(ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH)
        append_path = file_conversion_menu_options.selected_output_file_format[:-4]
        io.write(
            filename=append_path,
            images=loaded_atoms,
            format=file_conversion_menu_options.selected_output_file_format,
        )


# make menu items
# can use lambda functions to change text of options as well :)
file_conversion_menu_items = [
    FunctionItem(
        "Change input file path",
        FileConversionFunctions.select_input_file_path,
    ),
    FunctionItem(
        "Change output file format",
        FileConversionFunctions.select_output_file_format,
    ),
    FunctionItem(
        "Convert file format",
        FileConversionFunctions.points_directory_to_aimall_on_compute,
    ),
]

# initialize menu
file_conversion_menu = ConsoleMenu(
    this_menu_options=file_conversion_menu_options,
    title=FILE_CONVERSION_MENU_DESCRIPTION.title,
    subtitle=FILE_CONVERSION_MENU_DESCRIPTION.subtitle,
    prologue_text=FILE_CONVERSION_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=FILE_CONVERSION_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=FILE_CONVERSION_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(file_conversion_menu, file_conversion_menu_items)
