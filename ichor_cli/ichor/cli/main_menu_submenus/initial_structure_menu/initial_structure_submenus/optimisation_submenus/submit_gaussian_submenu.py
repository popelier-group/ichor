from dataclasses import dataclass
from pathlib import Path

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
    user_input_free_flow,
    user_input_int,
    user_input_path,
    xyz_file_selected,
)
from ichor.core.files import GaussianOutput
from ichor.hpc.main.gaussian import (
    submit_gaussian_output_to_xyz,
    submit_gjfs,
    submit_single_gaussian_xyz,
)
from ichor.hpc.main.opt import single_geometry_optimisation_directory

SUBMIT_GAUSSIAN_MENU_DESCRIPTION = MenuDescription(
    "Submit Gaussian Menu",
    subtitle="Use this menu to optimise a single geometry with Gaussian.\n"
    "Once optimised, the file will be converted to .xyz for further analysis. \n",
)

SUBMIT_GAUSSIAN_MENU_DEFAULTS = {
    "default_method": "b3lyp",
    "default_basis_set": "6-31+g(d,p)",
    "default_number_of_cores": 2,
    "default_overwrite_existing": False,
    "default_gjf_path": "",
}


# dataclass used to store values for SubmitGaussianMenu
@dataclass
class SubmitGaussianMenuOptions(MenuOptions):
    selected_method: str
    selected_basis_set: str
    selected_number_of_cores: int
    selected_overwrite_existing: bool
    selected_gjf_path: str


# initialize dataclass for storing information for menu
submit_gaussian_menu_options = SubmitGaussianMenuOptions(
    *SUBMIT_GAUSSIAN_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitGaussianFunctions:
    @staticmethod
    def select_method():
        """Asks user to update the method for Gaussian"""
        submit_gaussian_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_gaussian_menu_options.selected_method
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation method selected {submit_gaussian_menu_options.selected_method}"
        )

    @staticmethod
    def select_basis_set():
        """Asks user to update the basis set."""
        submit_gaussian_menu_options.selected_basis_set = user_input_free_flow(
            "Enter basis set: ", submit_gaussian_menu_options.selected_basis_set
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation basis set selected {submit_gaussian_menu_options.selected_basis_set}"
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to update the number of cores for submission."""
        submit_gaussian_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_gaussian_menu_options.selected_number_of_cores,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation number of cores selected {submit_gaussian_menu_options.selected_number_of_cores}"
        )

    @staticmethod
    def select_overwrite_existing():
        """Asks user whether or not to overwrite an existing optimisation directory"""
        submit_gaussian_menu_options.selected_overwrite_existing = user_input_bool(
            "Overwrite existing optimisation directory (yes/no): ",
            submit_gaussian_menu_options.selected_overwrite_existing,
        )

    @staticmethod
    def xyz_to_gaussian_on_compute():
        """Converts a single xyz to gjf and submit to Gaussian on compute."""

        # the geometry is selected in the menu above this one, so it can still be unset
        # by the time a job is submitted from here
        if not xyz_file_selected(
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            "submit the optimisation to Gaussian",
            what="starting geometry",
            select_with="Use 'Select xyz file containing a single unoptimised geometry' in the Optimisation Menu above this one.",
        ):
            return

        keywords, method, basis_set, ncores, overwrite_existing = (
            ["opt"],
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_basis_set,
            submit_gaussian_menu_options.selected_number_of_cores,
            submit_gaussian_menu_options.selected_overwrite_existing,
        )

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        job_id = submit_single_gaussian_xyz(
            input_xyz_path=xyz_path,
            ncores=ncores,
            keywords=keywords,
            method=method,
            basis_set=basis_set,
            overwrite_existing=overwrite_existing,
        )

        optimisation_dir = single_geometry_optimisation_directory(
            xyz_path.stem, "gaussian"
        )

        # nothing was submitted because the optimisation directory already exists
        if job_id is None:
            print_summary_and_pause(
                "GAUSSIAN OPTIMISATION NOT SUBMITTED",
                {
                    "Structure": xyz_path,
                    "Optimisation directory": optimisation_dir,
                },
                [
                    "The optimisation directory already exists and overwriting was not "
                    "selected, so the existing optimisation has been left alone and "
                    "nothing was submitted.",
                    "Either select the overwrite option to replace it, or move/rename "
                    "the existing directory to keep both.",
                ],
            )
            return

        print_summary_and_pause(
            "GAUSSIAN OPTIMISATION SUBMITTED",
            {
                "Structure": xyz_path,
                "Optimisation directory": optimisation_dir,
                "Optimised geometry": (
                    optimisation_dir / f"{xyz_path.stem}_optimised.xyz"
                ),
                "Job ID": job_id.id if job_id else "not available",
                "Method": method,
                "Basis set": basis_set,
                "Keywords": ", ".join(keywords),
                "CPU cores": ncores,
                "Overwrite existing": overwrite_existing,
            },
            [
                "The xyz file has been converted to a gjf and submitted to Gaussian as "
                "a geometry optimisation at the level of theory above.",
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue).",
                "The final geometry is written out as the xyz file above once the job "
                "has finished, and is what the trajectory creation menus should then "
                "be pointed at.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Gaussian optimisation job submitted for {xyz_path}, results in {optimisation_dir}"
        )

    @staticmethod
    def submit_existing_gjf():
        """Asks user to input existing gjf file as input."""
        gjf_path = user_input_path("Enter .gjf path to submit existing Gaussian job: ")
        ichor.cli.global_menu_variables.SELECTED_GJF_PATH = Path(gjf_path).absolute()
        submit_gaussian_menu_options.selected_gjf_path = (
            ichor.cli.global_menu_variables.SELECTED_GJF_PATH
        )
        gjf_path = ichor.cli.global_menu_variables.SELECTED_GJF_PATH

        # the path is typed in above rather than being a setting of the menu, so pressing
        # enter at the prompt leaves it as the directory ichor is running in
        if not input_file_selected(
            gjf_path, "submit the Gaussian job", what="gjf file"
        ):
            return

        ncores = submit_gaussian_menu_options.selected_number_of_cores
        job_id = submit_gjfs([gjf_path], force_calculate_wfn=False, ncores=ncores)

        # write out the final geometry as an xyz file next to the gjf file
        # once the Gaussian job it comes from has finished
        optimised_xyz_path = gjf_path.with_name(f"{gjf_path.stem}_optimised.xyz")
        submit_gaussian_output_to_xyz(
            gaussian_output_path=gjf_path.with_suffix(GaussianOutput.get_filetype()),
            xyz_path=optimised_xyz_path,
            hold=job_id,
        )

        print_summary_and_pause(
            "GAUSSIAN JOB SUBMITTED",
            {
                "Input file": gjf_path,
                "Optimised geometry": optimised_xyz_path,
                "Job ID": job_id.id if job_id else "not available",
                "CPU cores": ncores,
            },
            [
                "The gjf file was submitted as it is, so the level of theory and the "
                "keywords are whatever the file itself says, not the settings of this "
                "menu.",
                "A second job is held behind this one to write the final geometry out "
                "as the xyz file above once Gaussian has finished, so both jobs will "
                "show in your batch system's queue.",
            ],
        )

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Gaussian optimisation job submitted for {gjf_path}"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_gaussian_menu_items = [
    FunctionItem(
        "Change method",
        SubmitGaussianFunctions.select_method,
    ),
    FunctionItem(
        "Change basis set",
        SubmitGaussianFunctions.select_basis_set,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitGaussianFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Overwrite existing optimisation directory (if one is already present)",
        SubmitGaussianFunctions.select_overwrite_existing,
    ),
    FunctionItem(
        "SUBMIT to Gaussian",
        SubmitGaussianFunctions.xyz_to_gaussian_on_compute,
    ),
    FunctionItem(
        "SUBMIT exisiting .gjf file",
        SubmitGaussianFunctions.submit_existing_gjf,
    ),
]

# initialize menu
submit_gaussian_menu = ConsoleMenu(
    this_menu_options=submit_gaussian_menu_options,
    title=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_gaussian_menu, submit_gaussian_menu_items)
