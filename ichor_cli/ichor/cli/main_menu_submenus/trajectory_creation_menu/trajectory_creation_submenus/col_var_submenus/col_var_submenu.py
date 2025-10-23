from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_free_flow,
)

import ichor.core.molecular_dynamics.metadynamics as mtd

COL_VAR_MENU_DEFAULTS = {
    "default_col_vars": [],
}

COL_VAR_MENU_DESCRIPTION = MenuDescription(
    "Collective Variable Menu",
    subtitle="Use this menu to define collective variables for metadynamics calculations with ASE/PLUMED.",
)


@dataclass
class ColVarMenuOptions(MenuOptions):

    collective_variables_list: list


col_var_menu_options = ColVarMenuOptions(*COL_VAR_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class ColVarMenuFunctions:

    shared_options=None

    @staticmethod
    def show_mol_info():
        """
        Display information on atoms in molecule / system.
        """
        mtd.print_molecule_data(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        answer = ""
        user_input_free_flow("Press enter to continue: ", answer)

    @staticmethod
    def draw_labeled_molecule():
        mtd.draw_labeled_molecule(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

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

        print("\n\n----END OF MOLECULE INFORMATION----")
        print("Input collective variables (max 4 atoms per CV).\n2 = Distance, 3 = Angle, 4 = Dihedral \nPress Enter or 'q' to finish a CV.")

        while True:
            col_var = []
            print(f"\nDefine a new collective variable (you've entered {len(all_col_vars)} so far):")

            while len(col_var) < 4:
                user_input = input(f"  Enter atom ID {len(col_var)+1}: ").strip()

                if user_input == '' or user_input.lower() == 'q':
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
                    print("  You've already picked that atom in this collective variable.")
                    continue
                
                col_var.append(num)

            if len(col_var) >= 2:
                all_col_vars.append(col_var)
                if len(col_var) == 2:
                    print(f"  DISTANCE collective variable saved: {col_var}")
                elif len(col_var) == 3:
                    print(f"  ANGLE collective variable saved: {col_var}")
                elif len(col_var) == 4:
                    print(f"  DIHEDRAL collective variable saved: {col_var}")
            else:
                print("  Not enough atoms entered. Skipping CV.")
                break
            
            # Ask if user wants to enter another CV
            next_CV = input("Do you want to define another variable? (y/n): ").strip().lower()
            if next_CV != 'y':
                break
            
        print("\nAll collective variables collected:")
        print(all_col_vars)
        if ColVarMenuFunctions.shared_options:
            ColVarMenuFunctions.shared_options.collective_variables = all_col_vars
        
        answer = ""
        user_input_free_flow("Press enter to continue: ", answer)



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
        "Display system information",
        ColVarMenuFunctions.show_mol_info,
    ),
    FunctionItem(
        "Output labelled molecule image",
        ColVarMenuFunctions.draw_labeled_molecule,
    ),
    FunctionItem(
        "Define collective variables for metadynamics",
        ColVarMenuFunctions.select_col_vars,
    ),
]

add_items_to_menu(col_var_menu, col_var_menu_items)
