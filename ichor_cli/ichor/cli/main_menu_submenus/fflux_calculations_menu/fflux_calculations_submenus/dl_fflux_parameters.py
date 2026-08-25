"""The DL_POLY simulation parameters shared by the DL_FFLUX menus.

A single molecule run and a condensed phase run are set up very differently (one is a
molecule in an empty box, the other a periodic box packed to a density), so they have a
menu each - but the simulation itself is described by the same handful of settings. Those
live here, as a menu built around whichever menu's options dataclass is handed to it, so
that the two menus cannot drift apart.
"""

from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.useful_functions import (
    user_input_float,
    user_input_int,
    user_input_restricted,
)

# available DL_POLY ensembles that the menus expose
DL_FFLUX_ENSEMBLES = ["nvt", "nve"]

# the simulation settings both DL_FFLUX menus start from. A menu's own defaults dictionary
# is built on top of these, adding whatever else it needs.
DL_POLY_PARAMETER_DEFAULTS = {
    "default_ensemble": "nvt",
    "default_temperature": 300,
    "default_timestep": 0.001,
    "default_number_of_timesteps": 500,
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    "default_cutoff": 0.0,
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    "default_force_cap": 0.0,
}

DL_POLY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "DL_POLY Parameters Menu",
    subtitle="Change the DL_POLY simulation parameters for the DL_FFLUX calculation.",
)


def make_dl_poly_parameters_menu(options, cutoff_help: str) -> ConsoleMenu:
    """Builds the menu for changing the DL_POLY simulation parameters of a DL_FFLUX
    calculation.

    The menu has no options dataclass of its own: its items edit the options of the menu it
    was built for (which the parent menu's prologue displays), so the submit function of
    that menu keeps reading the same values.

    :param options: The options dataclass of the DL_FFLUX menu the parameters belong to. It
        must hold ``selected_ensemble``, ``selected_temperature``, ``selected_timestep``,
        ``selected_number_of_timesteps``, ``selected_cutoff`` and ``selected_force_cap``.
    :param cutoff_help: What entering 0 for the real-space cutoff does, which differs
        between the menus: a single molecule sizes its cutoff from the molecule and grows
        its box around it, while a condensed phase box is a fixed size and has its cutoff
        fitted to it.
    :return: The parameters menu, to be added to the parent menu as a ``SubmenuItem``.
    """

    def select_ensemble():
        """Select the DL_POLY ensemble (NVT or NVE)."""
        options.selected_ensemble = user_input_restricted(
            DL_FFLUX_ENSEMBLES,
            "Select ensemble: ",
            options.selected_ensemble,
        )

    def select_temperature():
        """Select the temperature of the DL_FFLUX simulation."""
        options.selected_temperature = user_input_int(
            "Select temperature: ", options.selected_temperature
        )

    def select_timestep():
        """Select the timestep (in ps) of the DL_FFLUX simulation."""
        options.selected_timestep = user_input_float(
            "Select timestep (ps): ", options.selected_timestep
        )

    def select_number_of_timesteps():
        """Select the number of timesteps of the DL_FFLUX simulation."""
        options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps: ",
            options.selected_number_of_timesteps,
        )

    def select_cutoff():
        """Select the real-space cutoff (in Angstrom) for the CONTROL cutoff/rvdw and the
        FFLUX.in electrostatics cut directives."""
        options.selected_cutoff = user_input_float(
            f"Select real-space cutoff in Angstrom (0 = {cutoff_help}): ",
            options.selected_cutoff,
        )

    def select_force_cap():
        """Select the force cap (in kT/Angstrom) applied during equilibration. This keeps a
        far-from-equilibrium run (e.g. one using inaccurate FFLUX models) from exploding.
        Enter 0 to disable force capping."""
        options.selected_force_cap = user_input_float(
            "Select force cap in kT/Angstrom (0 = disabled): ",
            options.selected_force_cap,
        )

    menu = ConsoleMenu(
        title=DL_POLY_PARAMETERS_MENU_DESCRIPTION.title,
        subtitle=DL_POLY_PARAMETERS_MENU_DESCRIPTION.subtitle,
        prologue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.prologue_description_text,
        epilogue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.epilogue_description_text,
        show_exit_option=DL_POLY_PARAMETERS_MENU_DESCRIPTION.show_exit_option,
    )

    add_items_to_menu(
        menu,
        [
            FunctionItem("Select ensemble (NVT / NVE)", select_ensemble),
            FunctionItem("Select simulation temperature", select_temperature),
            FunctionItem("Select timestep", select_timestep),
            FunctionItem("Select number of timesteps", select_number_of_timesteps),
            FunctionItem(
                f"Select real-space cutoff (Angstrom, 0 = {cutoff_help})", select_cutoff
            ),
            FunctionItem(
                "Select force cap (kT/Angstrom, 0 = disabled)", select_force_cap
            ),
        ],
    )

    return menu
