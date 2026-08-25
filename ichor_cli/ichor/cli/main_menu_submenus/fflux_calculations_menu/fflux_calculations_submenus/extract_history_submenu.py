from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    input_file_selected,
    print_summary_and_pause,
    user_input_bool,
    user_input_int,
    user_input_path,
)
from ichor.core.analysis import subsample_history

# what a timestep option is set to when it is not being used, as 0 is a timestep of the
# run itself (the geometry the run was started from) and so cannot mean "not set"
NOT_SET = -1

# what the output trajectory is called when the HISTORY file is selected before an output
# path has been given, written next to the HISTORY file it is taken out of
DEFAULT_OUTPUT_NAME = "sub_history.xyz"

EXTRACT_HISTORY_MENU_DEFAULTS = {
    # every timestep of the file, i.e. the whole trajectory, which is rarely what is
    # wanted but is the one default which throws nothing away
    "default_stride": 1,
    "default_first_timestep": 0,
    "default_overwrite_existing": False,
}

EXTRACT_HISTORY_MENU_DESCRIPTION = MenuDescription(
    "Extract Geometries From HISTORY Menu",
    subtitle="Use this to write geometries of a finished DL_FFLUX run out as an .xyz "
    "trajectory.",
)


@dataclass
class ExtractHistoryMenuOptions(MenuOptions):
    # HISTORY trajectory written by a finished DL_FFLUX run
    selected_history_path: Path
    # .xyz file the extracted geometries are written to
    selected_output_xyz_path: Path
    # every timestep whose number divides by this is written out
    selected_stride: int = EXTRACT_HISTORY_MENU_DEFAULTS["default_stride"]
    # the part of the run the geometries are taken from, e.g. to leave out the
    # equilibration at the start of it. None as the last timestep means the end of the run
    selected_first_timestep: int = EXTRACT_HISTORY_MENU_DEFAULTS[
        "default_first_timestep"
    ]
    selected_last_timestep: Optional[int] = None
    # a single timestep to write instead of a strided selection (None = use the stride)
    selected_exact_timestep: Optional[int] = None
    # write only the final geometry of the run, e.g. to restart from where it got to
    selected_only_final_timestep: bool = False
    selected_overwrite_existing: bool = EXTRACT_HISTORY_MENU_DEFAULTS[
        "default_overwrite_existing"
    ]

    def get_display_value(self, value):
        """Displays the timestep options which are not being used as ``not set``, rather
        than as ``None``."""
        if value is None:
            return "not set"
        return super().get_display_value(value)

    def check_selected_history_path(self) -> Union[str, None]:
        """Checks whether the given HISTORY file exists and is a file."""
        history_path = Path(self.selected_history_path)
        if not history_path.exists():
            return f"Current HISTORY path: {history_path} does not exist."
        elif not history_path.is_file():
            return f"Current HISTORY path: {history_path} is not a file."

    def check_selected_output_xyz_path(self) -> Union[str, None]:
        """Checks that the geometries are written somewhere they can be read back as a
        trajectory, and that an existing file is not about to be replaced without the
        overwrite option having been turned on."""
        output_path = Path(self.selected_output_xyz_path)
        if output_path.is_dir():
            return f"Current output path: {output_path} is a directory, not a file."
        elif output_path.suffix != ".xyz":
            return f"Current output path: {output_path} is not a .xyz file."
        elif output_path.exists() and not self.selected_overwrite_existing:
            return (
                f"Current output path: {output_path} already exists. Turn on the "
                "overwrite option or select another output path."
            )

    def check_selected_timesteps(self) -> Union[str, None]:
        """Warns when the timestep options which are set are not the ones which are used,
        as only one selection can be made at a time."""
        if self.selected_only_final_timestep:
            if self.selected_exact_timestep is not None:
                return (
                    "Only the final timestep is written, so the single timestep which "
                    "is selected is ignored."
                )
            return None
        if self.selected_exact_timestep is not None:
            if self.selected_exact_timestep < self.selected_first_timestep or (
                self.selected_last_timestep is not None
                and self.selected_exact_timestep > self.selected_last_timestep
            ):
                return (
                    "The single timestep which is selected is outside the range of "
                    "timesteps to extract from, so nothing would be written."
                )
        if (
            self.selected_last_timestep is not None
            and self.selected_last_timestep < self.selected_first_timestep
        ):
            return (
                "The last timestep to extract is before the first one, so nothing "
                "would be written."
            )


# initialize dataclass for storing information for menu
extract_history_menu_options = ExtractHistoryMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_PATH,
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH,
)


def _user_input_optional_int(prompt: str, current: Optional[int]) -> Optional[int]:
    """Asks for a timestep which does not have to be given, so that a timestep which was
    selected can be unselected again.

    :param prompt: The prompt to show, which should say what -1 does.
    :param current: The value which is kept when nothing is typed.
    :return: The timestep which was typed, or None if it was cleared.
    """

    answer = user_input_int(
        prompt, current if current is not None else NOT_SET, NOT_SET
    )

    if answer is None or answer == NOT_SET:
        return None

    return answer


# class with static methods for each menu item that calls a function.
class ExtractHistoryMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_history_path():
        """Select the HISTORY file to take the geometries out of, i.e. the trajectory a
        finished DL_FFLUX run wrote into its run directory. The output path is filled in
        next to it if one has not been given yet, and can be changed afterwards."""
        history_path = user_input_path("Enter HISTORY file path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_PATH = Path(
            history_path
        ).absolute()
        extract_history_menu_options.selected_history_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_PATH
        )

        # an output path which is still the directory ichor is running in has not been
        # given, so the geometries default to a file next to the run they come from
        if (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH
            == Path.cwd()
        ):
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH = (
                ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_PATH.parent
                / DEFAULT_OUTPUT_NAME
            )
            extract_history_menu_options.selected_output_xyz_path = (
                ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH
            )

    @staticmethod
    def select_output_xyz_path():
        """Select the .xyz file the extracted geometries are written to."""
        output_path = user_input_path("Enter output .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH = Path(
            output_path
        ).absolute()
        extract_history_menu_options.selected_output_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH
        )

    @staticmethod
    def select_stride():
        """Select how often a geometry is taken out of the run. Every timestep whose
        number divides by the stride is written, so a stride of 10000 on a million
        timestep run gives 100 geometries, however often the run printed to HISTORY."""
        extract_history_menu_options.selected_stride = user_input_int(
            "Select stride (in timesteps): ",
            extract_history_menu_options.selected_stride,
            1,
        )

    @staticmethod
    def select_first_timestep():
        """Select the timestep the extraction starts at, which is what leaves the
        equilibration at the start of a run out of the geometries taken from it."""
        extract_history_menu_options.selected_first_timestep = user_input_int(
            "Select first timestep to extract: ",
            extract_history_menu_options.selected_first_timestep,
            0,
        )

    @staticmethod
    def select_last_timestep():
        """Select the timestep the extraction stops at. Reading stops there as well, so
        this also cuts short the reading of a long HISTORY file."""
        extract_history_menu_options.selected_last_timestep = _user_input_optional_int(
            f"Select last timestep to extract ({NOT_SET} = end of the run): ",
            extract_history_menu_options.selected_last_timestep,
        )

    @staticmethod
    def select_exact_timestep():
        """Select a single timestep to write out instead of a strided selection, e.g. to
        pick out the geometry a run was at when something happened to it."""
        extract_history_menu_options.selected_exact_timestep = _user_input_optional_int(
            f"Select the one timestep to extract ({NOT_SET} = use the stride): ",
            extract_history_menu_options.selected_exact_timestep,
        )

    @staticmethod
    def select_only_final_timestep():
        """Choose whether only the final geometry of the run is written, which is what a
        further run is restarted from. This overrides the stride and the single timestep
        selection."""
        extract_history_menu_options.selected_only_final_timestep = user_input_bool(
            "Extract only the final timestep (yes/no): ",
            extract_history_menu_options.selected_only_final_timestep,
        )

    @staticmethod
    def select_overwrite_existing():
        """Choose whether an output file which is already there is replaced."""
        extract_history_menu_options.selected_overwrite_existing = user_input_bool(
            "Overwrite the output file if it exists (yes/no): ",
            extract_history_menu_options.selected_overwrite_existing,
        )

    @staticmethod
    def extract_geometries():
        """Streams the HISTORY file and writes the selected geometries out as an .xyz
        trajectory."""

        options = extract_history_menu_options
        history_path = ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_PATH
        output_path = Path(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_HISTORY_XYZ_PATH
        )

        # the HISTORY path defaults to the directory ichor is running in, which is not a
        # file, so without this the extraction fails on a path the user never chose
        if not input_file_selected(
            history_path,
            "extract geometries",
            what="HISTORY file",
            select_with="Use 'Select HISTORY file' in this menu first.",
        ):
            return

        if output_path.is_dir() or output_path == Path.cwd():
            print_summary_and_pause(
                "CANNOT EXTRACT GEOMETRIES",
                {"Output path": output_path, "Problem": "No output file was selected."},
                [
                    "Nothing has been done, as there is nowhere to write the geometries "
                    "to.",
                    "Use 'Select output trajectory (.xyz)' in this menu to give the "
                    "file the geometries are written to.",
                ],
            )
            return

        # writing over a trajectory which took an hour to extract, or over the geometries
        # a training set was made from, is worth asking about rather than just doing
        if output_path.exists() and not options.selected_overwrite_existing:
            print_summary_and_pause(
                "CANNOT EXTRACT GEOMETRIES",
                {
                    "Output path": output_path,
                    "Problem": f"{output_path} already exists.",
                },
                [
                    "Nothing has been done, as the file the geometries would be written "
                    "to is already there.",
                    "Either turn on the overwrite option in this menu, or select "
                    "another output path.",
                ],
            )
            return

        try:
            extracted = subsample_history(
                history_path,
                output_path,
                stride=options.selected_stride,
                min_step=options.selected_first_timestep,
                max_step=options.selected_last_timestep,
                exact_step=options.selected_exact_timestep,
                last_step_only=options.selected_only_final_timestep,
            )
        except (OSError, ValueError) as error:
            ichor.hpc.global_variables.LOGGER.error(
                f"Geometries not extracted from {history_path}: {error}"
            )
            print_summary_and_pause(
                "GEOMETRIES NOT EXTRACTED",
                {
                    "HISTORY file": history_path,
                    "Output path": output_path,
                    "Reason": error,
                },
                [
                    "A HISTORY file is the trajectory a DL_FFLUX run writes into its run "
                    "directory, which this reads timestep by timestep.",
                ],
            )
            return

        # which timesteps were asked for, in words, so that the summary says what was
        # extracted rather than only how much of it there was
        if options.selected_only_final_timestep:
            selection = "the final timestep only"
        elif options.selected_exact_timestep is not None:
            selection = f"timestep {options.selected_exact_timestep} only"
        else:
            selection = f"every timestep divisible by {options.selected_stride:,}"

        last_timestep = options.selected_last_timestep
        if last_timestep is None:
            timestep_range = (
                f"{options.selected_first_timestep:,} to the end of the run"
            )
        else:
            timestep_range = f"{options.selected_first_timestep:,} to {last_timestep:,}"

        if not extracted.ngeometries:
            print_summary_and_pause(
                "NO GEOMETRIES EXTRACTED",
                {
                    "HISTORY file": history_path,
                    "Timesteps read": f"{extracted.nframes_read:,}",
                    "Selection": selection,
                    "Timestep range": timestep_range,
                },
                [
                    "Nothing has been written, as no timestep of the HISTORY file "
                    "matched the selection, so any file at the output path has been "
                    "left as it was.",
                    "The timesteps are the ones the run printed to HISTORY (which is "
                    "not necessarily every timestep it ran), so a stride which is not a "
                    "multiple of the printing interval of the run matches nothing.",
                ],
            )
            return

        notes = [
            "The geometries are written in the order they were run, with the timestep "
            "each of them came from on its comment line.",
            "The trajectory can now be split into a PointsDirectory (Property "
            "Calculation Menu) or sampled down further (Trajectory Analysis Menu).",
        ]

        # timesteps DL_POLY wrote binary into cannot be read, which is worth saying, as
        # it is why a run can give fewer geometries than the stride says it should
        if extracted.nframes_skipped:
            notes.insert(
                0,
                f"{extracted.nframes_skipped:,} of the selected timesteps could not be "
                "read (DL_POLY occasionally writes binary into a HISTORY file) and were "
                "left out.",
            )

        print_summary_and_pause(
            "GEOMETRIES EXTRACTED",
            {
                "HISTORY file": history_path,
                "Output trajectory": output_path,
                "Geometries written": f"{extracted.ngeometries:,}",
                "Atoms per geometry": extracted.natoms,
                "First timestep written": f"{extracted.first_timestep:,}",
                "Last timestep written": f"{extracted.last_timestep:,}",
                "Timesteps read": f"{extracted.nframes_read:,}",
                "Selection": selection,
                "Timestep range": timestep_range,
            },
            notes,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Extracted {extracted.ngeometries} geometries from {history_path} "
            f"to {output_path}"
        )


# initialize menu
extract_history_menu = ConsoleMenu(
    this_menu_options=extract_history_menu_options,
    title=EXTRACT_HISTORY_MENU_DESCRIPTION.title,
    subtitle=EXTRACT_HISTORY_MENU_DESCRIPTION.subtitle,
    prologue_text=EXTRACT_HISTORY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=EXTRACT_HISTORY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=EXTRACT_HISTORY_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
extract_history_menu_items = [
    FunctionItem(
        "Select HISTORY file",
        ExtractHistoryMenuFunctions.select_history_path,
    ),
    FunctionItem(
        "Select output trajectory (.xyz)",
        ExtractHistoryMenuFunctions.select_output_xyz_path,
    ),
    FunctionItem(
        "Select stride (every timestep divisible by it is extracted)",
        ExtractHistoryMenuFunctions.select_stride,
    ),
    FunctionItem(
        "Select first timestep to extract",
        ExtractHistoryMenuFunctions.select_first_timestep,
    ),
    FunctionItem(
        f"Select last timestep to extract ({NOT_SET} = end of the run)",
        ExtractHistoryMenuFunctions.select_last_timestep,
    ),
    FunctionItem(
        f"Extract one timestep only ({NOT_SET} = use the stride)",
        ExtractHistoryMenuFunctions.select_exact_timestep,
    ),
    FunctionItem(
        "Extract only the final timestep of the run",
        ExtractHistoryMenuFunctions.select_only_final_timestep,
    ),
    FunctionItem(
        "Overwrite the output trajectory if it exists",
        ExtractHistoryMenuFunctions.select_overwrite_existing,
    ),
    FunctionItem(
        "Extract geometries to .xyz",
        ExtractHistoryMenuFunctions.extract_geometries,
    ),
]

add_items_to_menu(extract_history_menu, extract_history_menu_items)
