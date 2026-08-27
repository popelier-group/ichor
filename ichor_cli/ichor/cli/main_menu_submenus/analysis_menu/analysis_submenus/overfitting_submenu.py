from dataclasses import dataclass
from typing import Optional

from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.analysis_menu.analysis_submenus.model_analysis_common import (  # noqa: E501
    analysis_output_path,
    batch_system_is_set_up,
    discover_model_folders,
    models_directory_selected,
    no_batch_system_note,
    OVERFITTING_CSV_NAME,
    overfitting_submission_notes,
    pause,
    selected_models_path,
    selected_set_type,
    submit_overfitting_for_folders,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    maximum_cores,
    print_summary_and_pause,
    user_input_bool,
    user_input_int,
)
from ichor.core.analysis.model_metrics import write_metrics_per_element
from ichor.core.analysis.overfitting import overfitting_report, summarise_diagnoses
from ichor.core.models import Models

OVERFITTING_MENU_DESCRIPTION = MenuDescription(
    "Overfitting Check Menu",
    subtitle="Use this menu to check whether trained models are overfitting.\n",
)

OVERFITTING_MENU_DEFAULTS = {
    "default_number_of_cores": 16,
}


@dataclass
class OverfittingMenuOptions(MenuOptions):
    """The models directory and held-out split come from the Model Analysis Menu above
    this one, whose options are shown in the prologue as well, so the only setting of
    this menu is the size of the jobs it submits."""

    selected_number_of_cores: int

    def check_selected_number_of_cores(self) -> Optional[str]:
        """Checks that a submitted check asks for at least one core."""
        ncores = self.selected_number_of_cores
        if not isinstance(ncores, int) or ncores < 1:
            return f"Current number of cores: {ncores} must be 1 or greater."

    def check_number_of_cores_fits_machine(self) -> Optional[str]:
        """Checks that a submitted check does not ask for more cores than the machine
        can give it, as a job which asks for more is refused by the batch system."""
        ncores = self.selected_number_of_cores
        if not isinstance(ncores, int):
            return None

        largest = maximum_cores()
        if largest and ncores > largest:
            return (
                f"Current number of cores: {ncores:,} is more than the {largest:,} a "
                "job can ask for on this machine."
            )

    def check_batch_system_is_set_up(self) -> Optional[str]:
        """Warns when there is no queue to submit the check to, as that is what the
        first option of this menu does."""
        if not batch_system_is_set_up():
            return (
                "No batch system found, so the check cannot be submitted. Only the "
                "option which runs it here will work."
            )


overfitting_menu_options = OverfittingMenuOptions(*OVERFITTING_MENU_DEFAULTS.values())


class OverfittingFunctions:
    """Functions that run when overfitting menu items are selected."""

    @staticmethod
    def select_number_of_cores():
        """Asks how many cores each submitted overfitting job asks for.

        Every model is checked independently of every other, and the check of one is
        numpy work that a single core does, so the cores are what makes the job faster
        rather than only what gives it memory."""

        largest = maximum_cores()
        if largest:
            print(f"\nA job can ask for up to {largest:,} cores on this machine.\n")

        overfitting_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            overfitting_menu_options.selected_number_of_cores,
            minimum=1,
        )

    @staticmethod
    def submit_overfitting_check():
        """Submits the overfitting check of every model batch under the selected path
        to the queue, one job per batch.

        The check inverts the training covariance matrix of every model, so it runs for
        far longer than the rest of the model analysis and is not work for a login
        node. Each report is written next to the rest of that batch's analysis."""

        # a parent folder of model batches holds no models of its own, so only the
        # choice of the directory is checked here; the batches in it are found below
        if not models_directory_selected("submit the overfitting check", False):
            return

        if not batch_system_is_set_up():
            print_summary_and_pause(
                "OVERFITTING CHECK NOT SUBMITTED",
                {"Models path": selected_models_path()},
                [no_batch_system_note()],
            )
            return

        root = selected_models_path()
        model_folders = discover_model_folders(root)
        if not model_folders:
            pause(f"No model folders (containing .model files) found under {root}.")
            return

        ncores = overfitting_menu_options.selected_number_of_cores
        submitted, failed = submit_overfitting_for_folders(model_folders, ncores)

        if not submitted:
            print_summary_and_pause(
                "OVERFITTING CHECK NOT SUBMITTED",
                {
                    "Models path": root,
                    "Model folders tried": len(model_folders),
                },
                [
                    "None of the overfitting jobs could be submitted. The error given "
                    "for each of them is printed above this summary."
                ],
            )
            return

        print_summary_and_pause(
            "OVERFITTING CHECK SUBMITTED",
            {
                "Models path": root,
                "Held-out split": selected_set_type(),
                "Jobs submitted": f"{len(submitted)} of {len(model_folders)}",
                "CPU cores per job": ncores,
            },
            overfitting_submission_notes(ncores)
            + (
                [f"{len(failed)} model folder(s) could not be submitted."]
                if failed
                else []
            ),
        )

    @staticmethod
    def run_overfitting_check_here():
        """Runs the overfitting check on the selected models here and now, rather than
        submitting it.

        Each model is scored against itself by closed-form leave-one-out cross
        validation on the training data stored in its own ``.model`` file, and against
        the held-out FEREBUS CSVs of the selected split. Comparing the two, alongside
        how large the model says its own uncertainty is, separates a model which has
        memorised its training set from one which is merely being asked about parts of
        configuration space the training set never covered.

        This blocks the menu until it finishes, which for a large batch is a long time;
        the option above submits it instead."""

        if not models_directory_selected("check for overfitting"):
            return

        models_path = selected_models_path()
        models = Models(models_path)
        set_type = selected_set_type()
        csv_files = sorted(models_path.rglob(f"*_{set_type}.csv"))

        # the leave-one-out half of the check needs nothing but the models themselves,
        # so it is still worth running when no held-out CSVs were found
        if not csv_files:
            print(
                f"No '{set_type}' CSV files found under {models_path}.\n"
                "Reporting leave-one-out cross validation only; without a held-out "
                "set there is nothing to compare it against."
            )
            set_type = ""

        ncores = overfitting_menu_options.selected_number_of_cores
        print(
            f"\nChecking {len(models)} model(s) on {ncores} core(s). This is the slow "
            "part of the analysis, so it may take a while.\n"
        )

        output_name = analysis_output_path(OVERFITTING_CSV_NAME)
        report_df = overfitting_report(
            models,
            csv_files_list=csv_files,
            split_name=set_type,
            output_location=output_name,
            ncores=ncores,
        )

        if report_df.empty:
            pause("No models could be checked.")
            return

        print(report_df.to_string(index=False))
        print()
        print(summarise_diagnoses(report_df))

        written = [output_name]
        per_element = user_input_bool(
            "Also write a per-element-type breakdown? (y/n) [default no]: ",
            default=False,
        )
        if per_element:
            written += write_metrics_per_element(report_df, output_name)

        pause(f"{len(written)} overfitting report(s) written (e.g. {output_name}).")


overfitting_menu_items = [
    FunctionItem(
        "Submit the overfitting check to the queue",
        OverfittingFunctions.submit_overfitting_check,
    ),
    FunctionItem(
        "Run the overfitting check here (slow, blocks the menu)",
        OverfittingFunctions.run_overfitting_check_here,
    ),
    FunctionItem(
        "Change number of cores",
        OverfittingFunctions.select_number_of_cores,
    ),
]

overfitting_menu = ConsoleMenu(
    this_menu_options=overfitting_menu_options,
    title=OVERFITTING_MENU_DESCRIPTION.title,
    subtitle=OVERFITTING_MENU_DESCRIPTION.subtitle,
    prologue_text=OVERFITTING_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=OVERFITTING_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=OVERFITTING_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(overfitting_menu, overfitting_menu_items)
