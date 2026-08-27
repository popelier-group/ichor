import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.analysis_menu.analysis_submenus.model_analysis_common import (  # noqa: E501
    analysis_output_path,
    ANALYSIS_SUBFOLDER,
    batch_system_is_set_up,
    discover_model_folders,
    EXTERNAL_SET_TYPE,
    largest_training_set,
    INTERNAL_SET_TYPE,
    METRICS_CSV_NAME,
    models_directory_selected,
    no_batch_system_note,
    selected_models_path,
    selected_set_type,
    overfitting_submission_notes,
    overfitting_worker_memory_gb,
    pause,
    S_CURVES_CSV_NAME,
    S_CURVES_EXCEL_NAME,
    S_CURVES_PLOT_NAME,
    submit_overfitting_for_folders,
    workers_that_fit,
)
from ichor.cli.main_menu_submenus.analysis_menu.analysis_submenus.overfitting_submenu import (  # noqa: E501
    overfitting_menu,
    overfitting_menu_options,
    OVERFITTING_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    directory_selected,
    print_summary_and_pause,
    user_input_bool,
    user_input_free_flow,
    user_input_path,
)
from ichor.core.analysis.model_metrics import (
    metrics_df_from_total_dict,
    write_metrics_per_element,
)
from ichor.core.analysis.s_curves.compact_s_curves import (
    plot_s_curves_per_element,
    plot_with_matplotlib,
    simplified_write_to_excel,
    true_predicted_from_ferebus_csvs,
    write_s_curves_to_csv,
    write_s_curves_to_csv_per_element,
    write_s_curves_to_excel_per_element,
)
from ichor.core.files.ferebus import ExtractModelsScript
from ichor.core.models import Models
from tqdm import tqdm

# TODO - element type averages
# TODO - xyz to extract atom types - Bienfait

MODEL_ANALYSIS_MENU_DESCRIPTION = MenuDescription(
    "Model Analysis Menu",
    subtitle="Use this menu to make S-curves and extract quality metrics for trained models.\n",
)

MODEL_ANALYSIS_MENU_DEFAULTS = {
    "default_models_path": ichor.cli.global_menu_variables.SELECTED_MODELS_PATH,
    "default_set_type": EXTERNAL_SET_TYPE,
}


def _discover_seq_folders(root: Path) -> List[Path]:
    """Finds SEQ folders (containing trained models) under ``root``. A SEQ folder
    is a directory whose parent is a ``TRAIN-*`` folder and which contains at least
    one ``.model`` file. If ``root`` is itself such a SEQ folder, it is returned on
    its own.

    :param root: A training-run folder, e.g. a ``5_TRAINING`` tree, a system folder,
        a ``TRAIN-<n>`` folder, or a single SEQ folder.
    :return: A sorted list of SEQ folder paths that contain models.
    """

    root = Path(root)
    if not root.is_dir():
        return []

    if root.parent.name.startswith("TRAIN-"):
        candidates = [root]
    else:
        candidates = [
            d
            for d in tqdm(root.rglob("*"), desc="Scanning for SEQ folders")
            if d.is_dir() and d.parent.name.startswith("TRAIN-")
        ]

    # only keep folders that actually contain models (i.e. completed training)
    return sorted(
        d
        for d in tqdm(candidates, desc="Checking for model files")
        if any(d.rglob("*.model"))
    )


# dataclass used to store the state of the model analysis menu
@dataclass
class ModelAnalysisMenuOptions(MenuOptions):
    selected_models_path: Path
    selected_set_type: str

    def check_selected_models_path(self):
        """Checks whether the selected models path contains ``.model`` files."""
        models_path = Path(self.selected_models_path)
        if not models_path.is_dir():
            return "Current models path is not a directory."
        if not Models.check_path(models_path):
            return f"Current path {models_path} does not contain any .model files."


# initialize dataclass for storing information for the menu
model_analysis_menu_options = ModelAnalysisMenuOptions(
    *MODEL_ANALYSIS_MENU_DEFAULTS.values()
)


def _get_models_and_csv_files():
    """Builds the ``Models`` instance and the list of held-out CSV file paths from
    the currently selected models path. The held-out CSVs are co-located under the
    model folder (in ``test_set``/``valid_set`` subfolders, written there by the
    extract step), so they are found by searching the model folder recursively and
    filtering to the selected held-out split (external or internal validation)."""

    models_root = selected_models_path()
    models = Models(models_root)

    set_type = selected_set_type()
    csv_files = sorted(models_root.rglob(f"*_{set_type}.csv"))

    return models, csv_files


def _error_dict_from_total_dict(total_dict: dict) -> dict:
    """Reduces a nested ``{property: {atom: {"true", "predicted", "error"}}}`` dict
    to the ``{property: {atom: {"error": array}}}`` form the S-curve plotters need."""
    return {
        property_name: {
            atom: {"error": atom_data["error"]} for atom, atom_data in atom_dict.items()
        }
        for property_name, atom_dict in total_dict.items()
    }


def _report_saved_plots(saved_files):
    """Tells the user how many per-property S-curve files were written."""
    if saved_files:
        first = Path(saved_files[0]).absolute()
        pause(
            f"{len(saved_files)} S-curve plot(s) written, one per property "
            f"(e.g. {first})."
        )
    else:
        pause(
            "No S-curve plots written (matplotlib may be missing or there was no "
            "data)."
        )


def _prompt_s_curve_format() -> str:
    """Asks the user which S-curve output format to produce. Returns one of
    ``"excel"``, ``"matplotlib"`` or ``"csv"`` (defaulting to Excel)."""
    answer = user_input_free_flow(
        "Output format - (e)xcel workbook / (m)atplotlib images / (c)sv data only? "
        "[default excel]: "
    )
    if answer is not None:
        first = answer.strip().lower()[:1]
        if first == "m":
            return "matplotlib"
        if first == "c":
            return "csv"
    return "excel"


def _report_written_files(written, noun: str):
    """Tells the user how many output files were written (and an example), or that
    nothing was written."""
    if written:
        pause(
            f"{len(written)} {noun} written " f"(e.g. {Path(written[0]).absolute()})."
        )
    else:
        pause(f"No {noun} written (no data).")


def _warn_no_csv_files():
    """Warns the user that no CSV files matched the selected split."""
    pause(
        f"No '{selected_set_type()}' CSV files found "
        f"under {selected_models_path()}. "
        "Check that the held-out CSVs are co-located with the models and that the "
        "split is correct."
    )


def _prepare_ferebus_analysis(action: str):
    """Validates inputs, gathers models and held-out CSVs, and builds the nested
    ``total_dict`` of true/predicted/error values. Returns ``(models, total_dict)``
    or ``None`` if inputs are invalid or no CSVs matched the selected split.

    :param action: What the option which is being run would do, e.g. ``"make the
        S-curves"``, used in the message when the models have not been selected.
    """

    if not models_directory_selected(action):
        return None

    models, csv_files = _get_models_and_csv_files()
    if not csv_files:
        _warn_no_csv_files()
        return None

    total_dict = true_predicted_from_ferebus_csvs(csv_files, models)
    return models, total_dict


class ModelAnalysisFunctions:
    """Functions that run when model analysis menu items are selected."""

    @staticmethod
    def extract_models_from_run():
        """Runs the model-extraction script on a completed training run, copying
        the ``.model`` files and held-out CSVs from each SEQ folder into
        ``6_MODELS/<system>/<SEQ>/`` (with CSVs in ``test_set/`` and ``valid_set/``).
        The selected folder can be a whole ``5_TRAINING`` tree, a system folder, a
        ``TRAIN-<n>`` folder, or a single SEQ folder."""

        run_path = Path(
            user_input_path("Enter path to completed training run: ")
        ).absolute()

        # the run folder is typed rather than kept as a menu selection, so pressing
        # ctrl+D at the prompt gives the directory ichor is running in, every file of
        # which would then be walked looking for SEQ folders
        if not directory_selected(
            run_path,
            "extract the models",
            what="training run folder",
            select_with="Run this option again and enter the path of the completed "
            "training run.",
        ):
            return

        seq_folders = _discover_seq_folders(run_path)

        if not seq_folders:
            pause(f"No SEQ folders containing models found under {run_path}.")
            return

        print(f"Found {len(seq_folders)} SEQ folder(s) with models.")
        succeeded, failed = 0, 0
        for seq_folder in seq_folders:
            # the extraction script requires "5_TRAINING" in the path to locate
            # the destination 6_MODELS folder
            if "5_TRAINING" not in seq_folder.parts:
                print(f"Skipping {seq_folder}: not under a '5_TRAINING' folder.")
                failed += 1
                continue

            # write the (self-contained) extraction script into the SEQ folder and
            # run it there so it copies models + CSVs into 6_MODELS
            script_path = seq_folder / (
                "extract_models" + ExtractModelsScript.get_filetype()
            )
            ExtractModelsScript(script_path).write()

            try:
                subprocess.run(
                    [sys.executable, script_path.name],
                    cwd=str(seq_folder),
                    check=True,
                )
                succeeded += 1
            except subprocess.CalledProcessError as err:
                print(f"Extraction failed for {seq_folder}: {err}")
                failed += 1

        pause(
            f"Extraction finished: {succeeded} succeeded, {failed} failed.\n"
            "Models and held-out CSVs copied into 6_MODELS."
        )

    @staticmethod
    def select_models_directory():
        """Asks the user for the directory containing ``.model`` files. The held-out
        CSVs are co-located under this folder (in ``test_set``/``valid_set``
        subfolders, written there by the extract step) and are found automatically,
        so no separate CSV folder needs to be selected."""
        models_path = user_input_path("Enter path to models directory: ")
        ichor.cli.global_menu_variables.SELECTED_MODELS_PATH = Path(
            models_path
        ).absolute()
        model_analysis_menu_options.selected_models_path = (
            ichor.cli.global_menu_variables.SELECTED_MODELS_PATH
        )

    @staticmethod
    def select_set_type():
        """Lets the user choose which held-out split to evaluate: the external
        (EXT_VALIDATION_SET) or internal (INT_VALIDATION_SET) validation set."""
        answer = user_input_free_flow(
            "Evaluate which split - (e)xternal/test or (i)nternal/valid? "
            "[default external]: "
        )
        if answer is not None and answer.strip().lower().startswith("i"):
            set_type = INTERNAL_SET_TYPE
        else:
            set_type = EXTERNAL_SET_TYPE

        model_analysis_menu_options.selected_set_type = set_type
        # kept in the global as well, so the submenus of this menu are run against the
        # same split without having to reach into this menu's options
        ichor.cli.global_menu_variables.SELECTED_MODEL_SET_TYPE = set_type

    @staticmethod
    def make_s_curves():
        """Makes S-curves from the selected models and the held-out FEREBUS CSVs of
        the selected split. Prompts at runtime for the output format (Excel workbook
        / matplotlib images / CSV data only) and whether to also write a
        per-element-type breakdown (a separate set of files for each element)."""

        result = _prepare_ferebus_analysis("make the S-curves")
        if result is None:
            return
        _, total_dict = result

        fmt = _prompt_s_curve_format()
        per_element = user_input_bool(
            "Also write a per-element-type breakdown? (y/n) [default no]: ",
            default=False,
        )

        if fmt == "excel":
            output_name = analysis_output_path(S_CURVES_EXCEL_NAME)
            simplified_write_to_excel(total_dict, output_name)
            written = [output_name]
            if per_element:
                written += write_s_curves_to_excel_per_element(total_dict, output_name)
            _report_written_files(written, "S-curve workbook(s)")

        elif fmt == "csv":
            output_name = analysis_output_path(S_CURVES_CSV_NAME)
            written = write_s_curves_to_csv(total_dict, saved_name=output_name)
            if per_element:
                written += write_s_curves_to_csv_per_element(
                    total_dict, saved_name=output_name
                )
            _report_written_files(written, "S-curve CSV(s)")

        else:  # matplotlib
            output_name = analysis_output_path(S_CURVES_PLOT_NAME)
            written = plot_with_matplotlib(total_dict, saved_name=output_name)
            if per_element:
                written += plot_s_curves_per_element(total_dict, saved_name=output_name)
            _report_saved_plots(written)

    @staticmethod
    def extract_metrics():
        """Writes a CSV of quality metrics (RMSE, MAE, R2, max error and error
        percentiles) per atom/property from the selected models and the held-out
        FEREBUS CSVs of the selected split. Prints the table, and prompts whether to
        also write a per-element-type breakdown (a separate CSV for each element,
        e.g. ``model_metrics_C.csv``, ``model_metrics_H.csv``)."""

        result = _prepare_ferebus_analysis("extract the quality metrics")
        if result is None:
            return
        _, total_dict = result

        output_name = analysis_output_path(METRICS_CSV_NAME)
        metrics_df = metrics_df_from_total_dict(total_dict, output_location=output_name)
        print(metrics_df.to_string(index=False))

        written = [output_name]
        per_element = user_input_bool(
            "Also write a per-element-type breakdown? (y/n) [default no]: ",
            default=False,
        )
        if per_element:
            written += write_metrics_per_element(metrics_df, output_name)

        _report_written_files(written, "metrics CSV(s)")

    @staticmethod
    def run_batch_analysis():
        """Runs CSV-based analysis (S-curve Excel + per-property plots + metrics
        CSV) on *every* model batch found under the selected models path - like the
        extract script runs over every SEQ folder. The overfitting check of each batch
        is submitted to the queue afterwards rather than run here, as it is far slower
        than the rest; when there is no batch system to submit it to, it is skipped and
        the user is told so. Each batch uses its own
        co-located held-out CSVs of the selected split (external/internal), and all
        outputs are prefixed with the batch identifier so nothing is overwritten.

        Point the models directory at a parent folder (e.g. ``6_MODELS`` or
        ``6_MODELS/<system>``) to analyse many batches at once, or at a single model
        folder to analyse just that one.
        """

        # a parent folder of model batches holds no models of its own, so only the
        # choice of the directory is checked here; the batches in it are found below
        if not models_directory_selected("run the analysis", holds_models=False):
            return

        root = selected_models_path()
        model_folders = discover_model_folders(root)
        if not model_folders:
            pause(f"No model folders (containing .model files) found under {root}.")
            return

        set_type = selected_set_type()
        print(f"Found {len(model_folders)} model batch(es) to analyse.")

        analysed, skipped = 0, 0
        analysed_folders = []
        for model_folder in model_folders:

            print(f"\n=== Analysing {model_folder} ===")
            # each batch's held-out CSVs are co-located under it (test_set/valid_set)
            csv_files = sorted(model_folder.rglob(f"*_{set_type}.csv"))
            if not csv_files:
                print(
                    f"Skipping {model_folder}: no '{set_type}' CSVs found "
                    "(expected co-located test_set/valid_set)."
                )
                skipped += 1
                continue

            models = Models(model_folder)
            # predict once, then reuse for excel, plots and metrics
            total_dict = true_predicted_from_ferebus_csvs(csv_files, models)

            # S-curve Excel workbook
            excel_out = analysis_output_path(S_CURVES_EXCEL_NAME, model_folder)
            simplified_write_to_excel(total_dict, excel_out)

            # per-property S-curve images (plotter only needs the errors), plus a
            # per-element set (each element's atoms in their own file)
            error_dict = _error_dict_from_total_dict(total_dict)
            plot_out = analysis_output_path(S_CURVES_PLOT_NAME, model_folder)
            plot_with_matplotlib(error_dict, saved_name=plot_out)
            plot_s_curves_per_element(error_dict, saved_name=plot_out)

            # quality metrics CSV (combined, plus one CSV per element type)
            metrics_out = analysis_output_path(METRICS_CSV_NAME, model_folder)
            metrics_df = metrics_df_from_total_dict(
                total_dict, output_location=metrics_out
            )
            write_metrics_per_element(metrics_df, metrics_out)

            analysed += 1
            analysed_folders.append(model_folder)

        # the overfitting check is the slow half of the analysis (it inverts the
        # training covariance matrix of every model), so it is queued rather than run
        # here, once the batches it is checking are known
        submitted, failed_to_submit = [], []
        if not analysed_folders:
            overfitting_notes = []
        elif batch_system_is_set_up():
            print(
                f"\nSubmitting the overfitting check of {len(analysed_folders)} "
                "batch(es).\n"
            )
            ncores = overfitting_menu_options.selected_number_of_cores
            # what one check of these batches needs, so the jobs do not run more of them
            # at once than their memory holds
            workers = workers_that_fit(
                ncores,
                overfitting_worker_memory_gb(*largest_training_set(analysed_folders)),
            )
            submitted, failed_to_submit = submit_overfitting_for_folders(
                analysed_folders, ncores, workers=workers
            )
            overfitting_notes = overfitting_submission_notes(ncores, workers)
        else:
            overfitting_notes = [
                f"The overfitting check was skipped. {no_batch_system_note()}"
            ]

        print_summary_and_pause(
            "BATCH ANALYSIS COMPLETE",
            {
                "Models path": root,
                "Held-out split": set_type,
                "S-curves and metrics written": (
                    f"{analysed} of {len(model_folders)} batches"
                ),
                "Batches skipped": skipped,
                "Overfitting checks queued": (
                    f"{len(submitted)} job(s), one per batch"
                    if submitted
                    else "none (see below)"
                ),
            },
            [
                "The S-curves and quality metrics are done and written into each "
                f"batch's own {ANALYSIS_SUBFOLDER} folder.",
                *overfitting_notes,
                *(
                    [
                        f"{len(failed_to_submit)} overfitting job(s) could not be "
                        "submitted; the error given for each is printed above."
                    ]
                    if failed_to_submit
                    else []
                ),
            ],
        )


# make menu items
model_analysis_menu_items = [
    FunctionItem(
        "Extract models from a completed run",
        ModelAnalysisFunctions.extract_models_from_run,
    ),
    FunctionItem(
        "Select models directory",
        ModelAnalysisFunctions.select_models_directory,
    ),
    FunctionItem(
        "Select held-out split: external/test or internal/valid",
        ModelAnalysisFunctions.select_set_type,
    ),
    # analysis of the selected model folder using its held-out CSVs
    FunctionItem(
        "Make S-curves (choose Excel / matplotlib / CSV at runtime)",
        ModelAnalysisFunctions.make_s_curves,
    ),
    FunctionItem(
        "Extract quality metrics (CSV)",
        ModelAnalysisFunctions.extract_metrics,
    ),
    # Batch: run analysis on every model folder under the selected path
    FunctionItem(
        "[Batch] Run all analysis under the selected path",
        ModelAnalysisFunctions.run_batch_analysis,
    ),
]

# initialize menu
model_analysis_menu = ConsoleMenu(
    this_menu_options=model_analysis_menu_options,
    title=MODEL_ANALYSIS_MENU_DESCRIPTION.title,
    subtitle=MODEL_ANALYSIS_MENU_DESCRIPTION.subtitle,
    prologue_text=MODEL_ANALYSIS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=MODEL_ANALYSIS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=MODEL_ANALYSIS_MENU_DESCRIPTION.show_exit_option,
)

# the overfitting check is a submenu rather than an option, as it is submitted to the
# queue with settings of its own. It sits directly underneath the batch analysis, which
# submits it for every batch it analyses.
model_analysis_menu_items.append(
    SubmenuItem(
        OVERFITTING_MENU_DESCRIPTION.title,
        overfitting_menu,
        model_analysis_menu,
    )
)

add_items_to_menu(model_analysis_menu, model_analysis_menu_items)
