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
    "default_output_extension": "xyz",
}

# dataclass used to store values for FileConversionMenu


@dataclass
class FileConversionMenuOptions(MenuOptions):
    selected_input_file_path: Path
    selected_output_file_format: str
    selected_output_file_extension: str

    def check_selected_file_path(self) -> Union[str, None]:
        """Checks whether the given file exists."""
        inp_path = Path(self.selected_input_file_path)
        if not inp_path.exists():
            return f"Current file path: {inp_path} does not exist."
        elif not inp_path.is_file():
            return f"Current file path: {inp_path} is not a file."


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

        inp_path = user_input_path("Change input file path: ")
        ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH = Path(
            inp_path
        ).absolute()
        file_conversion_menu_options.selected_input_file_path = Path(
            inp_path
        ).absolute()

    @staticmethod
    def select_output_file_format():
        """Asks user to select the output file format eg mol, xyz."""
        # build expanded list to also include file extensions
        file_extensions = []
        extension_options = []
        # construct a list of file extensions for all files where they differ from file types
        # append an empty string for those without extensions to keep track of corresponding file type index
        for i in AVAILABLE_WRITE_FILE_FORMATS:
            if len(io.formats.ioformats[i].extensions) > 0:
                file_extensions.append(str(io.formats.ioformats[i].extensions[0]))
                extension_options.append(str(io.formats.ioformats[i].extensions[0]))
            else:
                file_extensions.append(i)

        # combine the lists to have both extensions and filetypes from ASE
        # Allows users to select by name or extension
        # Skips empty extensions in full extension list
        combined_list = AVAILABLE_WRITE_FILE_FORMATS + extension_options

        # invoke function to choose file
        chosen_format = user_input_restricted(
            combined_list,
            "Choose an output file format from these supported types: ",
            file_conversion_menu_options.selected_output_file_format,
        )
        # code to find which output suffix to append
        # check if file was chosen from file type
        if chosen_format in AVAILABLE_WRITE_FILE_FORMATS:
            # find file index that corresponds to chosen file type
            file_index = AVAILABLE_WRITE_FILE_FORMATS.index(chosen_format)
            # save file format extension
            format_ext = file_extensions[file_index]

        # check if file is in file extension list instead
        elif chosen_format in file_extensions:
            # save file format
            format_ext = chosen_format
            # find index that corresponds to matching file extension
            file_index = file_extensions.index(chosen_format)
            chosen_format = AVAILABLE_WRITE_FILE_FORMATS[file_index]

        # update file format name for required for ASE function
        file_conversion_menu_options.selected_output_file_format = chosen_format
        # update file extension required for naming file correctly
        file_conversion_menu_options.selected_output_file_extension = format_ext

    @staticmethod
    def convert_file():
        """Converts file from input to selected output format."""
        # read in data to ase from file
        loaded_atoms = io.read(ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH)
        # finds path to input file
        input_path = Path(
            file_conversion_menu_options.selected_input_file_path
        ).absolute()
        # append extension to .
        output_suffix = (
            "." + file_conversion_menu_options.selected_output_file_extension
        )
        # append the suffix to path
        output_path = input_path.with_suffix(output_suffix).absolute()
        # write file to location with new format and new suffix
        io.write(
            filename=str(output_path),
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
        FileConversionFunctions.convert_file,
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
