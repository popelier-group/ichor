from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables

import ichor.core.molecular_dynamics.metadynamics as mtd
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import print_summary_and_pause

COL_VAR_MENU_DESCRIPTION = MenuDescription(
    "Collective Variable Menu",
    subtitle="Use this menu to define collective variables for metadynamics calculations with ASE/PLUMED.",
)

# a collective variable is a list of atom IDs, and how many of them there are is what
# makes it a distance, an angle or a dihedral
COL_VAR_TYPES = {2: "DISTANCE", 3: "ANGLE", 4: "DIHEDRAL"}


def describe_collective_variable(col_var) -> str:
    """Describes a collective variable (a list of atom IDs) by its type and the atoms it
    is defined over, e.g. ``DISTANCE(0-1)``, so that it can be shown to the user without
    them having to work out what a bare list of atom IDs means.

    :param col_var: A list of the atom IDs the collective variable is defined over.
    :return: A readable description of the collective variable.
    """

    col_var_type = COL_VAR_TYPES.get(len(col_var), "UNKNOWN")
    atoms = "-".join(str(atom_id) for atom_id in col_var)
    return f"{col_var_type}({atoms})"


@dataclass
class ColVarMenuOptions(MenuOptions):
    pass


col_var_menu_options = ColVarMenuOptions()


# class with static methods for each menu item that calls a function.
class ColVarMenuFunctions:
    shared_options = None

    @staticmethod
    def select_col_vars():
        """
        Select number of CVs for metadynamics simulation.
        """
        # print info first for reference
        mtd.print_molecule_data(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)
        print("\n")
        atom_count = mtd.count_atoms(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        # Define range for atoms - 0 index with rdkit
        max_val = atom_count - 1

        # Master list to hold all collective variable sequences
        all_col_vars = []

        print("\n\n----END OF MOLECULE INFORMATION----\n\n")
        print(
            "Input collective variables (max 4 atoms per CV).\n2 = Distance, 3 = Angle, 4 = Dihedral \nPress Enter or 'q' to finish a CV.\n"
        )

        while True:
            col_var = []
            print(
                f"\nDefine a new collective variable (you've entered {len(all_col_vars)} so far):"
            )

            while len(col_var) < 4:
                user_input = input(f"  Enter atom ID {len(col_var) + 1}: ").strip()

                if user_input == "" or user_input.lower() == "q":
                    print("  Saving this collective variable.")
                    break

                if not user_input.isdigit():
                    print("  Please enter a valid integer.")
                    continue

                num = int(user_input)
                if num < 0 or num > max_val:
                    print(f"  AtomID must be between {0} and {max_val}.")
                    continue

                if num in col_var:
                    print(
                        "  You've already picked that atom in this collective variable."
                    )
                    continue

                col_var.append(num)

            if len(col_var) >= 2:
                all_col_vars.append(col_var)
                print(
                    f"  {describe_collective_variable(col_var)} collective variable "
                    f"saved: {col_var}"
                )
            else:
                print("  Not enough atoms entered. Skipping CV.")
                break

            # Ask if user wants to enter another CV
            next_CV = (
                input("Do you want to define another variable? (y/n): ").strip().lower()
            )
            if next_CV != "y":
                break

        if ColVarMenuFunctions.shared_options:
            ColVarMenuFunctions.shared_options.collective_variables = all_col_vars

        if not all_col_vars:
            print_summary_and_pause(
                "NO COLLECTIVE VARIABLES DEFINED",
                {"Structure": ichor.cli.global_menu_variables.SELECTED_XYZ_PATH},
                [
                    "No collective variable was saved, so the metadynamics menu still "
                    "has none to bias along and a job cannot be submitted yet.",
                    "A collective variable needs at least two atom IDs: enter 2 for a "
                    "distance, 3 for an angle or 4 for a dihedral, then press enter to "
                    "save it.",
                ],
            )
            return

        print_summary_and_pause(
            f"{len(all_col_vars)} COLLECTIVE VARIABLE(S) DEFINED",
            {
                "Structure": ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
                **{
                    f"Variable {i + 1}": (
                        f"{describe_collective_variable(col_var)}, atom IDs {col_var}"
                    )
                    for i, col_var in enumerate(all_col_vars)
                },
            },
            [
                "These are the variables the metadynamics run will deposit bias along. "
                "They are now held by the metadynamics menu and will be used by the "
                "next job submitted from it.",
                "Defining collective variables again replaces this set rather than "
                "adding to it, so enter all of the variables you want in one go.",
            ],
        )

    @staticmethod
    def show_mol_info():
        """
        Display information on atoms in molecule / system.
        """
        xyz_path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        mtd.print_molecule_data(xyz_path)

        print_summary_and_pause(
            "MOLECULE INFORMATION SHOWN ABOVE",
            {"Structure": xyz_path},
            [
                "The listing above covers the atoms and their neighbours, rings, "
                "functional groups, rotatable bonds, hydrogen bonds and dihedrals of "
                "the selected structure.",
                "The atom IDs it gives are the ones to enter when defining a "
                "collective variable; note they are 0-indexed, so the first atom of "
                "the file is atom 0.",
            ],
        )

    @staticmethod
    def draw_labeled_molecule():
        xyz_path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        mtd.draw_labeled_molecule(xyz_path)

        print_summary_and_pause(
            "LABELLED MOLECULE IMAGE WRITTEN",
            {
                "Structure": xyz_path,
                "Image": Path(xyz_path).with_suffix(".png"),
            },
            [
                "The image is a 2D drawing of the molecule with every atom labelled by "
                "its element and 0-indexed atom ID, which is the ID to enter when "
                "defining a collective variable.",
            ],
        )


# initialize menu
col_var_menu = ConsoleMenu(
    this_menu_options=col_var_menu_options,
    title=COL_VAR_MENU_DESCRIPTION.title,
    subtitle=COL_VAR_MENU_DESCRIPTION.subtitle,
    prologue_text=COL_VAR_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=COL_VAR_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=COL_VAR_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
col_var_menu_items = [
    FunctionItem(
        "Define collective variables for metadynamics",
        ColVarMenuFunctions.select_col_vars,
    ),
    FunctionItem(
        "Display system information",
        ColVarMenuFunctions.show_mol_info,
    ),
    FunctionItem(
        "Output labelled molecule image",
        ColVarMenuFunctions.draw_labeled_molecule,
    ),
]

add_items_to_menu(col_var_menu, col_var_menu_items)
