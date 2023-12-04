from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.useful_functions import (
    bool_to_str,
    user_input_bool,
    user_input_free_flow,
    user_input_path,
)
from ichor.cli.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)
from ichor.core.atoms import ALF
from ichor.core.common.str import get_digits
from ichor.core.files import Trajectory, XYZ

ANALYSIS_MENU_DESCRIPTION = MenuDescription(
    "Analysis Menu", subtitle="Use this to do analysis of data with ichor."
)
analysis_menu = ConsoleMenu(
    title=ANALYSIS_MENU_DESCRIPTION.title,
    subtitle=ANALYSIS_MENU_DESCRIPTION.subtitle,
    prologue_text=ANALYSIS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=ANALYSIS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=ANALYSIS_MENU_DESCRIPTION.show_exit_option,
)


def is_atom_name_in_atom_names(atom_name, atom_names) -> bool:

    return atom_name in atom_names


def ask_user_input_for_atom_name(
    atom_names: list, atom_position: str, default_index: int
):

    while True:
        atom_name = user_input_free_flow(
            f"Select {atom_position} atom, default {atom_names[default_index]}: "
        ).upper()
        if is_atom_name_in_atom_names(atom_name, atom_names):
            return atom_name
        elif atom_name is None:
            atom_name = atom_names[default_index]
            return atom_name


class AnalysisFunctions:
    @staticmethod
    def give_xyz_file_and_center_trajectory_on_atom():
        """Asks for user input for an xyz file
        It reads the xyz file and lets you choose an atom to
        center on (as well as x-axis and xy-plane atoms).
        After that it writes out a new file that is centered
        on the given ALF.
        """

        default_submit_on_compute = False

        trajectory_path = user_input_path("Enter path to xyz: ")

        # get atom names from first geometry
        first_geometry = XYZ(trajectory_path)
        atom_names = first_geometry.atom_names
        print(f"Available atom names: {', '.join(atom_names)}")

        # get alf atoms to center on
        central_atom_name = ask_user_input_for_atom_name(atom_names, "central", 0)
        x_axis_atom_name = ask_user_input_for_atom_name(atom_names, "x-axis", 1)
        xy_plane_atom_name = ask_user_input_for_atom_name(atom_names, "xy-plane", 2)

        central_atom_index = get_digits(central_atom_name) - 1
        x_axis_index = get_digits(x_axis_atom_name) - 1
        xy_plane_index = get_digits(xy_plane_atom_name) - 1

        alf_dict = {
            central_atom_name: ALF(central_atom_index, x_axis_index, xy_plane_index)
        }

        submit_on_compute = user_input_bool(
            f"Submit to compute node (yes/no), default {bool_to_str(default_submit_on_compute)}: "
        )
        if submit_on_compute is None:
            submit_on_compute = default_submit_on_compute

        xyz_output_path = (
            f"{central_atom_name}_{x_axis_atom_name}_{xy_plane_atom_name}_centered.xyz"
        )

        if not submit_on_compute:

            traj = Trajectory(trajectory_path)
            traj.center_geometries_on_atom_and_write_xyz(
                central_atom_name, alf_dict, xyz_output_path
            )

        else:

            text_list = []
            # make the python command that will be written in the submit script
            # it will get executed as `python -c python_code_to_execute...`
            text_list.append("from ichor.core.files import Trajectory")
            text_list.append("from ichor.core.atoms import ALF")
            text_list.append(f"traj = Trajectory({trajectory_path})")
            text_list.append(
                f"traj.center_geometries_on_atom_and_write_xyz({central_atom_name}, {alf_dict}, {xyz_output_path})"
            )

            submit_free_flow_python_command_on_compute(
                text_list, "center_trajectory", 2
            )


analysis_menu_items = [
    FunctionItem(
        "Center xyz on atoms.",
        AnalysisFunctions.give_xyz_file_and_center_trajectory_on_atom,
    ),
]

add_items_to_menu(analysis_menu, analysis_menu_items)
