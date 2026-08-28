from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables

from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.trajectory_creation_menu.trajectory_creation_submenus.col_var_submenus.col_var_submenu import (
    col_var_menu,
    ColVarMenuFunctions,
    describe_collective_variable,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_bool,
    user_input_float,
    user_input_free_flow,
    user_input_int,
    xyz_file_selected,
)
from ichor.core.files.mtd import (
    DEFAULT_MD_RUNSTEPS,
    DEFAULT_NUMBER_OF_GEOMETRIES,
    geometry_write_interval,
    number_of_geometries_written,
)
from ichor.hpc.check_python_env import ConfiguredPythonEnvironmentError
from ichor.hpc.molecular_dynamics import prep_mtd, submit_mtd

METADYNAMICS_MENU_DEFAULTS = {
    "default_collective_variables": [],
    "default_timestep": 0.005,
    "default_md_runstep": DEFAULT_MD_RUNSTEPS,
    "default_number_of_geometries_to_write": DEFAULT_NUMBER_OF_GEOMETRIES,
    "default_bias_factor": 5,
    "default_number_of_iterations": 1024,
    "default_temperature": 300,
    "default_calculator": "GFN2-xTB",
    "overwrite": False,
    "ncores": 2,
}

METADYNAMICS_MENU_DESCRIPTION = MenuDescription(
    "Metadynamics Menu",
    subtitle="Use this to submit metadynamics simulations with ASE/PLUMED.",
)


@dataclass
class MetadynamicsMenuOptions(MenuOptions):
    collective_variables: list
    selected_timestep: float
    selected_md_runsteps: int
    # how many geometries the whole run writes out, which the interval between writes is
    # worked out from rather than being set directly
    selected_number_of_geometries_to_write: int
    selected_bias: float
    selected_number_of_iterations: int
    selected_temperature: float
    selected_calculator: str
    overwrite: bool
    ncores: int

    def check_number_of_geometries_to_write(self) -> Union[str, None]:
        """Warns when the settings cannot give the number of geometries asked for, as a
        run can write out at most one geometry per timestep."""

        if self.selected_number_of_geometries_to_write < 1:
            return (
                "Number of geometries to write out must be at least 1, otherwise the "
                "run produces no trajectory."
            )
        if self.selected_md_runsteps < 1:
            return "Number of MD timesteps must be at least 1."
        if self.selected_number_of_geometries_to_write > self.selected_md_runsteps:
            return (
                f"Only {self.selected_md_runsteps} geometries can be written out from "
                f"{self.selected_md_runsteps} MD timesteps, so every timestep will be "
                f"written rather than the {self.selected_number_of_geometries_to_write} "
                "asked for."
            )


metadynamics_menu_options = MetadynamicsMenuOptions(
    *METADYNAMICS_MENU_DEFAULTS.values()
)


# Inject shared options into submenu logic
ColVarMenuFunctions.shared_options = metadynamics_menu_options


# class with static methods for each menu item that calls a function.
class MetadynamicsMenuFunctions:
    @staticmethod
    def select_timestep():
        """
        Select timestep for metadynamics simulation.
        """
        metadynamics_menu_options.selected_timestep = user_input_float(
            "Select timestep (fs): ", metadynamics_menu_options.selected_timestep
        )

    def select_number_of_md_timesteps():
        """
        Select how many timesteps to run the MD calculation for.
        """
        metadynamics_menu_options.selected_md_runsteps = user_input_int(
            "Number of MD timesteps: ",
            metadynamics_menu_options.selected_md_runsteps,
            minimum=1,
        )

    @staticmethod
    def select_number_of_geometries_to_write():
        """
        Select how many geometries the run writes out in total. The geometries are spread
        evenly over the run: a run of 100,000 timesteps asked for 10,000 geometries writes
        one out every 10 timesteps. Asking for at least as many geometries as there are
        timesteps writes every timestep out, which is as often as a run can be sampled.
        """
        metadynamics_menu_options.selected_number_of_geometries_to_write = (
            user_input_int(
                "Number of geometries to write out: ",
                metadynamics_menu_options.selected_number_of_geometries_to_write,
                minimum=1,
            )
        )

    @staticmethod
    def select_bias_factor():
        """
        Selects bias factor for collective variables in a metadynamics simulation.
        """
        metadynamics_menu_options.selected_bias = user_input_float(
            "Select bias factor: ",
            metadynamics_menu_options.selected_bias,
        )

    @staticmethod
    def select_number_of_iterations():
        """
        Select how many iterations to run for in metadynamics simulation.
        """
        metadynamics_menu_options.selected_number_of_iterations = user_input_int(
            "Set number of simulation iterations: ",
            metadynamics_menu_options.selected_number_of_iterations,
            minimum=1,
        )

    @staticmethod
    def select_temperature():
        """
        Set the temperature for metadynamics calculation.
        """
        metadynamics_menu_options.selected_temperature = user_input_float(
            "Selected temperature (K): ", metadynamics_menu_options.selected_temperature
        )

    @staticmethod
    def select_calculator():
        """
        Select the calculator to use for metadynamics.
        """
        metadynamics_menu_options.selected_calculator = user_input_free_flow(
            "Select calculator: ", metadynamics_menu_options.selected_calculator
        )

    @staticmethod
    def select_overwrite():
        """
        Select the to overwrite existing calculation on current structure.
        """
        metadynamics_menu_options.overwrite = user_input_bool(
            "Overwrite existing calc: ", metadynamics_menu_options.overwrite
        )

    def select_number_of_cores():
        """
        Select how many cores required to run job.
        """
        metadynamics_menu_options.ncores = user_input_int(
            "Number of CPU cores: ", metadynamics_menu_options.ncores, minimum=1
        )

    @staticmethod
    def submit_metadynamics_to_compute():
        """Asks for user input and submits metadynamics job to compute node."""

        # the geometry the run starts from is selected in the menu above this one, so it
        # can still be unset by the time a job is submitted from here
        if not xyz_file_selected(
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            "set up the metadynamics run",
            what="starting geometry",
            select_with="Use 'Select xyz file containing a single optimised geometry' in the Trajectory Creation Menu above this one.",
        ):
            return

        # if no collective variables are defined then do nothing.
        if len(metadynamics_menu_options.collective_variables) == 0:
            print_summary_and_pause(
                "METADYNAMICS JOB NOT SUBMITTED",
                notes=[
                    "No collective variables are loaded. A metadynamics simulation "
                    "biases the system along its collective variables, so at least one "
                    "must be defined before a job can be set up.",
                    "Use 'Set up collective variables for metadynamics' to define a "
                    "distance, angle or dihedral between atoms of the selected "
                    "structure, then submit again.",
                ],
            )
            return
        # if they are present, then start the run for a metadynamics job
        else:
            col_vars = metadynamics_menu_options.collective_variables
            timestep = metadynamics_menu_options.selected_timestep
            md_runsteps = metadynamics_menu_options.selected_md_runsteps
            number_of_geometries = (
                metadynamics_menu_options.selected_number_of_geometries_to_write
            )
            bias = metadynamics_menu_options.selected_bias
            iterations = metadynamics_menu_options.selected_number_of_iterations
            temperature = metadynamics_menu_options.selected_temperature
            calculator = metadynamics_menu_options.selected_calculator
            overwrite = metadynamics_menu_options.overwrite
            ncores = metadynamics_menu_options.ncores

            mtd_script = prep_mtd(
                input_xyz_path=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
                collective_variables=col_vars,
                timestep=timestep,
                md_runsteps=md_runsteps,
                md_freq_out=number_of_geometries,
                bias_factor=bias,
                iterations=iterations,
                temperature=temperature,
                system_name=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH.stem,
                calculator=calculator,
                overwrite=overwrite,
            )
            xyz_path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
            run_directory = (
                Path(ichor.hpc.global_variables.FILE_STRUCTURE["metadynamics_traj"])
                / xyz_path.stem
            )

            # check if there is actually a mtd job to submit. prep_mtd returns None when
            # the run directory is already there and overwriting was not asked for
            if mtd_script is None:
                print_summary_and_pause(
                    "METADYNAMICS JOB NOT SUBMITTED",
                    {
                        "Starting geometry": xyz_path,
                        "Run directory": run_directory,
                    },
                    [
                        "The run directory already contains a metadynamics setup for "
                        "this structure and overwriting was not selected, so nothing "
                        "has been submitted and the existing run has been left alone.",
                        "Either select 'Select whether to overwrite existing "
                        "calculation' to replace it, or move/rename the existing "
                        "directory to keep both.",
                    ],
                )
                return

            # the conda environment the job would activate is not set up with what
            # the generated script imports, so nothing is submitted as the job
            # would fail on the compute node
            try:
                job_id = submit_mtd(
                    input_script=mtd_script,
                    script_name=ichor.hpc.global_variables.SCRIPT_NAMES["mtd"],
                    ncores=ncores,
                )
            except ConfiguredPythonEnvironmentError as e:
                ichor.hpc.global_variables.LOGGER.error(
                    f"Metadynamics job not submitted: {e}"
                )
                print_summary_and_pause(
                    "METADYNAMICS JOB NOT SUBMITTED",
                    {"Starting geometry": xyz_path, "Reason": e},
                    [
                        "The run drives xtb through ASE with PLUMED on the compute "
                        "node, in the conda environment named in the ichor config "
                        "file. That environment is not set up to run it, so the job "
                        "would have failed. Nothing has been submitted.",
                        "Follow the instructions above and try again. The run "
                        "directory has been left in place, so selecting overwrite "
                        "is not needed when you do.",
                    ],
                )
                return

            # describe the collective variables by type and the atoms they involve,
            # as they are what makes this run different from a plain MD run
            collective_variables = ", ".join(
                describe_collective_variable(cv) for cv in col_vars
            )

            # work out what the run will actually do with the number of geometries asked
            # for, which is not the same thing when more were asked for than the run has
            # timesteps to give
            write_interval = geometry_write_interval(md_runsteps, number_of_geometries)
            geometries_written = number_of_geometries_written(
                md_runsteps, write_interval
            )

            notes = [
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with "
                "your batch system's queue command (e.g. qstat / squeue).",
                "The PLUMED input, the trajectory and the accumulated bias "
                "(HILLS) are all written into the run directory above; the job's "
                "stdout and stderr end up in the outputs and errors directories.",
            ]
            # geometries can only be written a whole number of timesteps apart, so the
            # run rarely writes out exactly the number asked for. say so rather than
            # leaving the difference to be discovered in the finished trajectory
            if geometries_written != number_of_geometries:
                notes.insert(
                    0,
                    f"Note that {number_of_geometries:,} geometries were asked for but "
                    f"the run will write out about {geometries_written:,} of them: they "
                    "can only be written a whole number of timesteps apart, and "
                    f"{md_runsteps:,} timesteps works out at one every "
                    f"{write_interval:,}. Making the number of timesteps a multiple of "
                    "the number of geometries gives exactly the number asked for.",
                )

            print_summary_and_pause(
                "METADYNAMICS JOB SUBMITTED",
                {
                    "Starting geometry": xyz_path,
                    "Run directory": run_directory,
                    "Job ID": job_id.id if job_id else "not available",
                    "Collective variables": f"{len(col_vars)} ({collective_variables})",
                    "Calculator": calculator,
                    "Timestep": f"{timestep} fs",
                    "MD timesteps": f"{md_runsteps:,}",
                    "Geometries written": f"~{geometries_written:,} "
                    f"(one every {write_interval:,} timestep(s))",
                    "Calculator iterations": f"{iterations:,} (max per energy "
                    "evaluation)",
                    "Temperature": f"{temperature} K",
                    "Bias factor": bias,
                    "CPU cores": ncores,
                    "Overwrite existing": overwrite,
                },
                notes,
            )
            # update logger
            ichor.hpc.global_variables.LOGGER.info(
                "Metadynamics trajectory generation job submitted"
            )


# initialize menu
metadynamics_menu = ConsoleMenu(
    this_menu_options=metadynamics_menu_options,
    title=METADYNAMICS_MENU_DESCRIPTION.title,
    subtitle=METADYNAMICS_MENU_DESCRIPTION.subtitle,
    prologue_text=METADYNAMICS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=METADYNAMICS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=METADYNAMICS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
metadynamics_menu_items = [
    SubmenuItem(
        "Set up collective variables for metadynamics", col_var_menu, metadynamics_menu
    ),
    FunctionItem(
        "Select timestep (fs)",
        MetadynamicsMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select number of MD timesteps ",
        MetadynamicsMenuFunctions.select_number_of_md_timesteps,
    ),
    FunctionItem(
        "Select number of geometries to write out",
        MetadynamicsMenuFunctions.select_number_of_geometries_to_write,
    ),
    FunctionItem(
        "Select bias factor for collective variables",
        MetadynamicsMenuFunctions.select_bias_factor,
    ),
    FunctionItem(
        "Select number of iterations",
        MetadynamicsMenuFunctions.select_number_of_iterations,
    ),
    FunctionItem(
        "Select simulation temperature (K)",
        MetadynamicsMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select calculator to use for metadynamics",
        MetadynamicsMenuFunctions.select_calculator,
    ),
    FunctionItem(
        "Select whether to overwrite existing calculation",
        MetadynamicsMenuFunctions.select_overwrite,
    ),
    FunctionItem(
        "Select how many CPU cores to use",
        MetadynamicsMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "SUBMIT metadynamics simulation",
        MetadynamicsMenuFunctions.submit_metadynamics_to_compute,
    ),
]

add_items_to_menu(metadynamics_menu, metadynamics_menu_items)
