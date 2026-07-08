import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_free_flow,
    user_input_path,
)
from ichor.core.analysis.model_metrics import (
    calculate_metrics_from_ferebus_csvs,
    calculate_model_metrics,
    get_true_predicted_dicts,
    metrics_df_from_total_dict,
)
from ichor.core.analysis.s_curves import calculate_s_curves
from ichor.core.analysis.s_curves.compact_s_curves import (
    mpl_get_true_vals_dict,
    plot_with_matplotlib,
    simplified_write_to_excel,
    true_predicted_from_ferebus_csvs,
)
from ichor.core.files.ferebus import ExtractModelsScript
from ichor.core.models import Models

# held-out split naming used in FEREBUS/ichor training CSV file names
EXTERNAL_SET_TYPE = "EXT_VALIDATION_SET"
INTERNAL_SET_TYPE = "INT_VALIDATION_SET"

MODEL_ANALYSIS_MENU_DESCRIPTION = MenuDescription(
    "Model Analysis Menu",
    subtitle="Use this menu to make S-curves and extract quality metrics for trained models.\n",
)

MODEL_ANALYSIS_MENU_DEFAULTS = {
    "default_models_path": ichor.cli.global_menu_variables.SELECTED_MODELS_PATH,
    "default_validation_set_path": ichor.cli.global_menu_variables.SELECTED_VALIDATION_SET_PATH,  # noqa: E501
    "default_test_csv_path": ichor.cli.global_menu_variables.SELECTED_TEST_CSV_PATH,
    "default_set_type": EXTERNAL_SET_TYPE,
    "default_property_types": None,
    "default_s_curves_output": "s-curves.xlsx",
    "default_plot_output": "s-curves.png",
    "default_metrics_output": "model_metrics.csv",
}

# subfolder names used when held-out CSVs are co-located inside a model folder
# (written there by the model-extraction step). Used to auto-fill the CSV path.
TEST_SET_SUBFOLDER = "test_set"
VALID_SET_SUBFOLDER = "valid_set"


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
            for d in root.rglob("*")
            if d.is_dir() and d.parent.name.startswith("TRAIN-")
        ]

    # only keep folders that actually contain models (i.e. completed training)
    return sorted(d for d in candidates if any(d.rglob("*.model")))


def _find_colocated_csv_folder(models_path: Path) -> Optional[Path]:
    """Returns the path to a co-located held-out CSV folder inside ``models_path``
    (preferring ``test_set`` over ``valid_set``), or ``None`` if neither exists
    with CSV files in it. CSVs may be nested in per-property subfolders, so the
    search is recursive."""

    for subfolder in (TEST_SET_SUBFOLDER, VALID_SET_SUBFOLDER):
        candidate = models_path / subfolder
        if candidate.is_dir() and any(candidate.rglob("*.csv")):
            return candidate
    return None


# dataclass used to store the state of the model analysis menu
@dataclass
class ModelAnalysisMenuOptions(MenuOptions):
    selected_models_path: Path
    selected_validation_set_path: Path
    selected_test_csv_path: Path
    selected_set_type: str
    selected_property_types: Optional[List[str]]
    selected_s_curves_output: str
    selected_plot_output: str
    selected_metrics_output: str

    def check_selected_models_path(self):
        """Checks whether the selected models path contains ``.model`` files."""
        models_path = Path(self.selected_models_path)
        if not models_path.is_dir():
            return "Current models path is not a directory."
        if not Models.check_path(models_path):
            return f"Current path {models_path} does not contain any .model files."

    def check_selected_validation_set_path(self):
        """Checks whether the selected validation set path is a directory."""
        validation_path = Path(self.selected_validation_set_path)
        if not validation_path.is_dir():
            return "Current validation set path is not a directory."

    def check_selected_test_csv_path(self):
        """Checks whether the selected CSV folder contains any .csv files (searched
        recursively, since FEREBUS CSVs live in per-property subfolders)."""
        csv_path = Path(self.selected_test_csv_path)
        if not csv_path.is_dir():
            return "Current CSV path is not a directory."
        if not any(csv_path.rglob("*.csv")):
            return f"Current path {csv_path} does not contain any .csv files."


# initialize dataclass for storing information for the menu
model_analysis_menu_options = ModelAnalysisMenuOptions(
    *MODEL_ANALYSIS_MENU_DEFAULTS.values()
)


def _paths_are_valid() -> bool:
    """Returns True if both the models path and validation set path are valid,
    otherwise prints why and returns False."""

    models_error = model_analysis_menu_options.check_selected_models_path()
    if models_error:
        user_input_free_flow(f"{models_error} Press enter to continue: ")
        return False

    validation_error = model_analysis_menu_options.check_selected_validation_set_path()
    if validation_error:
        user_input_free_flow(f"{validation_error} Press enter to continue: ")
        return False

    return True


def _csv_inputs_are_valid() -> bool:
    """Returns True if the models path and the test CSV folder are both valid,
    otherwise prints why and returns False."""

    models_error = model_analysis_menu_options.check_selected_models_path()
    if models_error:
        user_input_free_flow(f"{models_error} Press enter to continue: ")
        return False

    csv_error = model_analysis_menu_options.check_selected_test_csv_path()
    if csv_error:
        user_input_free_flow(f"{csv_error} Press enter to continue: ")
        return False

    return True


def _get_models_and_csv_files():
    """Builds the ``Models`` instance and the list of held-out CSV file paths from
    the currently selected models path and CSV folder. CSVs are searched
    recursively (they live in per-property subfolders) and filtered to the
    selected held-out split (external or internal validation)."""

    models = Models(Path(model_analysis_menu_options.selected_models_path))

    set_type = model_analysis_menu_options.selected_set_type
    csv_root = Path(model_analysis_menu_options.selected_test_csv_path)
    csv_files = sorted(csv_root.rglob(f"*_{set_type}.csv"))

    return models, csv_files


def _discover_model_folders(root: Path) -> List[Path]:
    """Finds model folders (directories that directly contain ``.model`` files)
    under ``root``. If ``root`` is itself a model folder it is returned on its own.
    Used to run analysis over a whole parent folder of model batches, e.g. every
    ``SEQ-XX-YY-ZZ`` folder under ``6_MODELS`` (the layout produced by the extract
    step)."""

    root = Path(root)
    if not root.is_dir():
        return []
    if Models.check_path(root):
        return [root]
    return sorted(d for d in root.rglob("*") if d.is_dir() and Models.check_path(d))


def _model_output_prefix(models_path: Optional[Path] = None) -> str:
    """Builds a filename-safe identifier for a models folder. For the standard
    ``6_MODELS/<system>/SEQ-XX-YY-ZZ`` layout this is ``<system>_SEQ-XX-YY-ZZ`` so
    outputs from different models or training splits do not overwrite each other.

    :param models_path: The models folder to build the identifier from. Defaults to
        the currently selected models path.
    """

    if models_path is None:
        models_path = model_analysis_menu_options.selected_models_path
    models_path = Path(models_path)
    seq_name = models_path.name
    system_name = models_path.parent.name

    # skip generic/degenerate path pieces
    skip = {"", ".", "..", "6_MODELS"}
    parts = [p for p in (system_name, seq_name) if p not in skip]
    return "_".join(parts) if parts else "model"


def _prefixed_output(base_name: str, models_path: Optional[Path] = None) -> str:
    """Prefixes ``base_name`` with the model identifier (see
    :func:`_model_output_prefix`), e.g. ``s-curves.xlsx`` ->
    ``<system>_SEQ-XX-YY-ZZ_s-curves.xlsx``."""

    return f"{_model_output_prefix(models_path)}_{base_name}"


def _report_saved_plots(saved_files):
    """Tells the user how many per-property S-curve files were written."""
    if saved_files:
        first = Path(saved_files[0]).absolute()
        user_input_free_flow(
            f"{len(saved_files)} S-curve plot(s) written, one per property "
            f"(e.g. {first}). Press enter to continue: "
        )
    else:
        user_input_free_flow(
            "No S-curve plots written (matplotlib may be missing or there was no "
            "data). Press enter to continue: "
        )


def _warn_no_csv_files():
    """Warns the user that no CSV files matched the selected split."""
    user_input_free_flow(
        f"No '{model_analysis_menu_options.selected_set_type}' CSV files found "
        f"under {model_analysis_menu_options.selected_test_csv_path}. "
        "Check the CSV folder and split. Press enter to continue: "
    )


def _prepare_ferebus_analysis():
    """Validates inputs, gathers models and held-out CSVs, and builds the nested
    ``total_dict`` of true/predicted/error values. Returns ``(models, total_dict)``
    or ``None`` if inputs are invalid or no CSVs matched the selected split."""

    if not _csv_inputs_are_valid():
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

        run_path = user_input_path("Enter path to completed training run: ")
        seq_folders = _discover_seq_folders(Path(run_path).absolute())

        if not seq_folders:
            user_input_free_flow(
                f"No SEQ folders containing models found under {run_path}. "
                "Press enter to continue: "
            )
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

        user_input_free_flow(
            f"Extraction finished: {succeeded} succeeded, {failed} failed. "
            "Models and held-out CSVs copied into 6_MODELS. Press enter to continue: "
        )

    @staticmethod
    def select_models_directory():
        """Asks the user for the directory containing ``.model`` files. If that
        folder contains co-located held-out CSVs (in a ``test_set`` or
        ``valid_set`` subfolder), the test CSV path is auto-filled to it."""
        models_path = user_input_path("Enter path to models directory: ")
        ichor.cli.global_menu_variables.SELECTED_MODELS_PATH = Path(
            models_path
        ).absolute()
        model_analysis_menu_options.selected_models_path = (
            ichor.cli.global_menu_variables.SELECTED_MODELS_PATH
        )

        # auto-fill the test CSV folder if held-out CSVs are co-located with the
        # models (see _find_colocated_csv_folder)
        colocated_csv_folder = _find_colocated_csv_folder(
            ichor.cli.global_menu_variables.SELECTED_MODELS_PATH
        )
        if colocated_csv_folder is not None:
            ichor.cli.global_menu_variables.SELECTED_TEST_CSV_PATH = (
                colocated_csv_folder
            )
            model_analysis_menu_options.selected_test_csv_path = colocated_csv_folder
            print(f"Auto-selected co-located CSV folder: {colocated_csv_folder}")

    @staticmethod
    def select_validation_set_directory():
        """Asks the user for the validation/test set PointsDirectory."""
        validation_path = user_input_path(
            "Enter path to validation/test set PointsDirectory: "
        )
        ichor.cli.global_menu_variables.SELECTED_VALIDATION_SET_PATH = Path(
            validation_path
        ).absolute()
        model_analysis_menu_options.selected_validation_set_path = (
            ichor.cli.global_menu_variables.SELECTED_VALIDATION_SET_PATH
        )

    @staticmethod
    def select_test_csv_directory():
        """Asks the user for the folder of held-out CSV files. This can be a model
        folder's ``test_set``/``valid_set`` subfolder, or a ``5_TRAINING`` SEQ
        folder; CSVs are searched recursively and filtered by the selected split."""
        csv_path = user_input_path(
            "Enter path to held-out CSV folder (searched recursively): "
        )
        ichor.cli.global_menu_variables.SELECTED_TEST_CSV_PATH = Path(
            csv_path
        ).absolute()
        model_analysis_menu_options.selected_test_csv_path = (
            ichor.cli.global_menu_variables.SELECTED_TEST_CSV_PATH
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
            model_analysis_menu_options.selected_set_type = INTERNAL_SET_TYPE
        else:
            model_analysis_menu_options.selected_set_type = EXTERNAL_SET_TYPE

    @staticmethod
    def select_property_types():
        """Asks the user for a comma-separated list of property types to restrict
        the analysis to (e.g. ``iqa, q00``). Leaving the prompt blank uses all
        property types found in the models."""

        answer = user_input_free_flow(
            "Enter comma-separated property types (e.g. iqa, q00), "
            "or leave blank for all: "
        )
        if answer is None:
            model_analysis_menu_options.selected_property_types = None
        else:
            types = [t.strip() for t in answer.split(",") if t.strip()]
            model_analysis_menu_options.selected_property_types = types or None

    @staticmethod
    def make_s_curves_excel():
        """Makes an Excel workbook of S-curves for the selected models and
        validation set."""

        if not _paths_are_valid():
            return

        output_name = _prefixed_output(
            model_analysis_menu_options.selected_s_curves_output
        )
        calculate_s_curves(
            model_location=Path(model_analysis_menu_options.selected_models_path),
            validation_set_location=Path(
                model_analysis_menu_options.selected_validation_set_path
            ),
            output_location=output_name,
            types=model_analysis_menu_options.selected_property_types,
        )
        user_input_free_flow(
            f"S-curves written to {Path(output_name).absolute()}. "
            "Press enter to continue: "
        )

    @staticmethod
    def make_s_curves_plot():
        """Saves matplotlib S-curve images for the selected models and validation
        set - one separate image file per property type."""

        if not _paths_are_valid():
            return

        true_dict, predicted_dict = get_true_predicted_dicts(
            model_location=Path(model_analysis_menu_options.selected_models_path),
            validation_set_location=Path(
                model_analysis_menu_options.selected_validation_set_path
            ),
            types=model_analysis_menu_options.selected_property_types,
        )
        total_dict = mpl_get_true_vals_dict(predicted_dict, true_dict)

        output_name = _prefixed_output(model_analysis_menu_options.selected_plot_output)
        saved_files = plot_with_matplotlib(total_dict, saved_name=output_name)
        _report_saved_plots(saved_files)

    @staticmethod
    def extract_metrics():
        """Writes a CSV of quality metrics (RMSE, MAE, R2, max error and error
        percentiles) per atom/property for the selected models and validation
        set. Also prints the table to the screen."""

        if not _paths_are_valid():
            return

        output_name = _prefixed_output(
            model_analysis_menu_options.selected_metrics_output
        )
        metrics_df = calculate_model_metrics(
            model_location=Path(model_analysis_menu_options.selected_models_path),
            validation_set_location=Path(
                model_analysis_menu_options.selected_validation_set_path
            ),
            output_location=output_name,
            types=model_analysis_menu_options.selected_property_types,
        )
        print(metrics_df.to_string(index=False))
        user_input_free_flow(
            f"Metrics written to {Path(output_name).absolute()}. "
            "Press enter to continue: "
        )

    @staticmethod
    def make_s_curves_excel_from_csvs():
        """Makes an Excel workbook of S-curves from the selected models and the
        held-out FEREBUS CSVs of the selected split."""

        result = _prepare_ferebus_analysis()
        if result is None:
            return
        _, total_dict = result

        output_name = _prefixed_output(
            model_analysis_menu_options.selected_s_curves_output
        )
        simplified_write_to_excel(total_dict, output_name)
        user_input_free_flow(
            f"S-curves written to {Path(output_name).absolute()}. "
            "Press enter to continue: "
        )

    @staticmethod
    def make_s_curves_plot_from_csvs():
        """Saves matplotlib S-curve images from the selected models and the held-out
        FEREBUS CSVs of the selected split - one separate image file per property."""

        result = _prepare_ferebus_analysis()
        if result is None:
            return
        _, total_dict = result

        # the plotter only needs the errors for each atom/property
        error_dict = {
            property_name: {
                atom: {"error": atom_data["error"]}
                for atom, atom_data in atom_dict.items()
            }
            for property_name, atom_dict in total_dict.items()
        }

        output_name = _prefixed_output(model_analysis_menu_options.selected_plot_output)
        saved_files = plot_with_matplotlib(error_dict, saved_name=output_name)
        _report_saved_plots(saved_files)

    @staticmethod
    def extract_metrics_from_csvs():
        """Writes a CSV of quality metrics (RMSE, MAE, R2, max error and error
        percentiles) per atom/property from the selected models and the held-out
        FEREBUS CSVs of the selected split. Also prints the table."""

        if not _csv_inputs_are_valid():
            return

        models, csv_files = _get_models_and_csv_files()
        if not csv_files:
            _warn_no_csv_files()
            return

        output_name = _prefixed_output(
            model_analysis_menu_options.selected_metrics_output
        )
        metrics_df = calculate_metrics_from_ferebus_csvs(
            csv_files_list=csv_files,
            models=models,
            output_location=output_name,
        )
        print(metrics_df.to_string(index=False))
        user_input_free_flow(
            f"Metrics written to {Path(output_name).absolute()}. "
            "Press enter to continue: "
        )

    @staticmethod
    def run_batch_analysis():
        """Runs CSV-based analysis (S-curve Excel + per-property plots + metrics
        CSV) on *every* model batch found under the selected models path - like the
        extract script runs over every SEQ folder. Each batch uses its own
        co-located held-out CSVs of the selected split (external/internal), and all
        outputs are prefixed with the batch identifier so nothing is overwritten.

        Point the models directory at a parent folder (e.g. ``6_MODELS`` or
        ``6_MODELS/<system>``) to analyse many batches at once, or at a single model
        folder to analyse just that one.
        """

        root = Path(model_analysis_menu_options.selected_models_path)
        model_folders = _discover_model_folders(root)
        if not model_folders:
            user_input_free_flow(
                f"No model folders (containing .model files) found under {root}. "
                "Press enter to continue: "
            )
            return

        set_type = model_analysis_menu_options.selected_set_type
        print(f"Found {len(model_folders)} model batch(es) to analyse.")

        analysed, skipped = 0, 0
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
            excel_out = _prefixed_output(
                model_analysis_menu_options.selected_s_curves_output, model_folder
            )
            simplified_write_to_excel(total_dict, excel_out)

            # per-property S-curve images (plotter only needs the errors)
            error_dict = {
                property_name: {
                    atom: {"error": atom_data["error"]}
                    for atom, atom_data in atom_dict.items()
                }
                for property_name, atom_dict in total_dict.items()
            }
            plot_out = _prefixed_output(
                model_analysis_menu_options.selected_plot_output, model_folder
            )
            plot_with_matplotlib(error_dict, saved_name=plot_out)

            # quality metrics CSV
            metrics_out = _prefixed_output(
                model_analysis_menu_options.selected_metrics_output, model_folder
            )
            metrics_df_from_total_dict(total_dict, output_location=metrics_out)

            analysed += 1

        user_input_free_flow(
            f"Batch analysis complete: {analysed} analysed, {skipped} skipped. "
            "Outputs are prefixed with each batch identifier. "
            "Press enter to continue: "
        )


# make menu items
model_analysis_menu_items = [
    FunctionItem(
        "Extract models + held-out CSVs from a completed run into 6_MODELS",
        ModelAnalysisFunctions.extract_models_from_run,
    ),
    FunctionItem(
        "Select models directory",
        ModelAnalysisFunctions.select_models_directory,
    ),
    FunctionItem(
        "Select validation/test set PointsDirectory",
        ModelAnalysisFunctions.select_validation_set_directory,
    ),
    FunctionItem(
        "Select held-out CSV folder (for [CSVs] options)",
        ModelAnalysisFunctions.select_test_csv_directory,
    ),
    FunctionItem(
        "Select held-out split: external/test or internal/valid (for [CSVs] options)",
        ModelAnalysisFunctions.select_set_type,
    ),
    FunctionItem(
        "Select property types (optional filter, PointsDirectory path only)",
        ModelAnalysisFunctions.select_property_types,
    ),
    # PointsDirectory-based analysis (general; supply a held-out-only PointsDirectory)
    FunctionItem(
        "[PointsDirectory] Make S-curves (Excel workbook)",
        ModelAnalysisFunctions.make_s_curves_excel,
    ),
    FunctionItem(
        "[PointsDirectory] Make S-curves (matplotlib image)",
        ModelAnalysisFunctions.make_s_curves_plot,
    ),
    FunctionItem(
        "[PointsDirectory] Extract quality metrics (CSV)",
        ModelAnalysisFunctions.extract_metrics,
    ),
    # CSV-based analysis (matches the train/valid/test CSV splits from data prep)
    FunctionItem(
        "[CSVs] Make S-curves (Excel workbook)",
        ModelAnalysisFunctions.make_s_curves_excel_from_csvs,
    ),
    FunctionItem(
        "[CSVs] Make S-curves (matplotlib image)",
        ModelAnalysisFunctions.make_s_curves_plot_from_csvs,
    ),
    FunctionItem(
        "[CSVs] Extract quality metrics (CSV)",
        ModelAnalysisFunctions.extract_metrics_from_csvs,
    ),
    # Batch: run CSV-based analysis on every model folder under the selected path
    FunctionItem(
        "[Batch] Run all analysis on every model folder under the selected path",
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

add_items_to_menu(model_analysis_menu, model_analysis_menu_items)
