from dataclasses import dataclass
from typing import Optional, Tuple

from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.analysis_menu.analysis_submenus.model_analysis_common import (  # noqa: E501
    analysis_output_path,
    batch_system_is_set_up,
    discover_model_folders,
    largest_training_set,
    models_directory_selected,
    models_in_largest_batch,
    no_batch_system_note,
    overfitting_worker_memory_gb,
    OVERFITTING_CSV_NAME,
    overfitting_submission_notes,
    pause,
    selected_models_path,
    selected_set_type,
    submit_overfitting_for_folders,
    workers_that_fit,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    format_memory_gb,
    job_memory_gb,
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


# What the last measurement of the selected batches found: how many models the biggest
# holds, and what one check of it needs. Filled in by _measure_batches, which reads model
# files, so that the checks below (which run every time the menu is drawn) do not.
_measured = {"models": 0, "ntrain": 0, "n_features": 0, "worker_gb": 0.0}


def _measure_batches() -> dict:
    """Reads the batches under the selected path, and remembers what they are.

    One model is read per batch, which is what makes this too slow to do while drawing
    the menu, so it is done when an option which needs it is picked and remembered for
    the warnings.
    """

    model_folders = discover_model_folders(selected_models_path())
    ntrain, n_features = largest_training_set(model_folders)

    _measured.update(
        models=models_in_largest_batch(model_folders),
        ntrain=ntrain,
        n_features=n_features,
        worker_gb=overfitting_worker_memory_gb(ntrain, n_features),
    )

    return _measured


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

    def check_models_checked_at_once_fits_memory(self) -> Optional[str]:
        """Warns when a job of this many cores cannot check one model per core, because
        one check of a training set this size needs more memory than one core brings.

        The job is still worth submitting: it asks for the cores (which is how the batch
        system gives it their memory) and checks fewer models at a time. This says so,
        rather than leaving the job to be killed for running out of memory.
        """

        ncores = self.selected_number_of_cores
        worker_gb = _measured["worker_gb"]
        if not isinstance(ncores, int) or ncores < 1 or worker_gb <= 0.0:
            return None

        workers = workers_that_fit(ncores, worker_gb)
        if workers >= ncores:
            return None

        return (
            f"One check of a {_measured['ntrain']:,} point training set needs "
            f"{format_memory_gb(worker_gb)}, so a {ncores} core job "
            f"({job_memory_gb(ncores):,.0f} GB) can only check {workers} at once "
            f"rather than one per core. It will still be submitted, and will still ask "
            f"for {ncores} cores to be given that memory."
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


def _suggest_number_of_cores() -> Tuple[int, int]:
    """Works out how many cores the overfitting jobs can put to use.

    The unit of work is one model, i.e. one (atom, property) pair, so a job has no use
    for more cores than the batch it checks has models: a 20 atom system with iqa and
    its multipole moments has a few hundred of them, which is far more than the atom
    count and usually more than the machine allows a job to ask for.

    :return: (the models in the biggest batch under the selected path, the cores to
        suggest). Both are 0 when no batches were found, e.g. when the models directory
        has not been selected yet.
    """

    measured = _measure_batches()
    model_count = measured["models"]

    if not model_count:
        return 0, 0

    largest = maximum_cores()

    return model_count, (min(model_count, largest) if largest else model_count)


class OverfittingFunctions:
    """Functions that run when overfitting menu items are selected."""

    @staticmethod
    def select_number_of_cores():
        """Asks how many cores each submitted overfitting job asks for.

        Every model is checked independently of every other, and the check of one is
        numpy work that a single core does, so the cores are what makes the job faster
        rather than only what gives it memory. One core per model is therefore what
        there is any use for, and that is what is suggested; the models under the
        selected path are counted to work it out."""

        largest = maximum_cores()
        model_count, suggested = _suggest_number_of_cores()

        # one short line each, as this is printed just above the prompt
        if model_count:
            print(f"\n{model_count:,} models in the largest batch under the selected")
            print("path, and one model is checked per core, so cores past")
            print(f"{suggested:,} would sit idle.")
            if largest and model_count > largest:
                print(f"This machine allows {largest:,} cores, fewer than the models.")

            worker_gb = _measured["worker_gb"]
            if worker_gb:
                fitting = workers_that_fit(suggested, worker_gb)
                print(
                    f"One check of its {_measured['ntrain']:,} training points needs "
                    f"{format_memory_gb(worker_gb)},"
                )
                if fitting < suggested:
                    print(
                        f"so {suggested:,} cores would run only {fitting:,} checks at "
                        "once."
                    )
                else:
                    print("which one core's memory holds.")
            print("")
        else:
            print("\nNo model folders found under the selected path (select one in")
            print("the Model Analysis Menu), so the number of models is not known.")
            if largest:
                print(f"A job can ask for up to {largest:,} cores on this machine.")
            print("")

        # pressing enter takes the suggestion, or keeps the current setting when there
        # is nothing to suggest from
        default = suggested or overfitting_menu_options.selected_number_of_cores
        overfitting_menu_options.selected_number_of_cores = user_input_int(
            f"Enter number of cores [default {default:,}]: ",
            default,
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
        # what the batches need, so the jobs do not run more checks at once than their
        # memory holds
        _measure_batches()
        workers = workers_that_fit(ncores, _measured["worker_gb"])
        submitted, failed = submit_overfitting_for_folders(
            model_folders, ncores, workers=workers
        )

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
                "CPU cores per job": (
                    f"{ncores} ({job_memory_gb(ncores):,.0f} GB of memory)"
                ),
                "Models checked at once": workers,
            },
            overfitting_submission_notes(ncores, workers)
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
        worker_gb = overfitting_worker_memory_gb(*largest_training_set([models_path]))
        needs = f" One check needs {format_memory_gb(worker_gb)}." if worker_gb else ""
        print(
            f"\nChecking {len(models)} model(s) on {ncores} core(s) of this machine."
            f"{needs}\nThis is the slow part of the analysis, so it may take a "
            "while.\n"
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
