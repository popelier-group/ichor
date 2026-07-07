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
    calculate_model_metrics,
    get_true_predicted_dicts,
)
from ichor.core.analysis.s_curves import calculate_s_curves
from ichor.core.analysis.s_curves.compact_s_curves import (
    mpl_get_true_vals_dict,
    plot_with_matplotlib,
)
from ichor.core.models import Models

MODEL_ANALYSIS_MENU_DESCRIPTION = MenuDescription(
    "Model Analysis Menu",
    subtitle="Use this menu to make S-curves and extract quality metrics for trained models.\n",
)

MODEL_ANALYSIS_MENU_DEFAULTS = {
    "default_models_path": ichor.cli.global_menu_variables.SELECTED_MODELS_PATH,
    "default_validation_set_path": ichor.cli.global_menu_variables.SELECTED_VALIDATION_SET_PATH,  # noqa: E501
    "default_property_types": None,
    "default_s_curves_output": "s-curves.xlsx",
    "default_plot_output": "s-curves.svg",
    "default_metrics_output": "model_metrics.csv",
}


# dataclass used to store the state of the model analysis menu
@dataclass
class ModelAnalysisMenuOptions(MenuOptions):
    selected_models_path: Path
    selected_validation_set_path: Path
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


class ModelAnalysisFunctions:
    """Functions that run when model analysis menu items are selected."""

    @staticmethod
    def select_models_directory():
        """Asks the user for the directory containing ``.model`` files."""
        models_path = user_input_path("Enter path to models directory: ")
        ichor.cli.global_menu_variables.SELECTED_MODELS_PATH = Path(
            models_path
        ).absolute()
        model_analysis_menu_options.selected_models_path = (
            ichor.cli.global_menu_variables.SELECTED_MODELS_PATH
        )

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

        output_name = model_analysis_menu_options.selected_s_curves_output
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
        """Saves a matplotlib image of the S-curves for the selected models and
        validation set. One subplot is made per property type, so restrict the
        property types first if the models contain many properties."""

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

        output_name = model_analysis_menu_options.selected_plot_output
        plot_with_matplotlib(total_dict, saved_name=output_name)
        user_input_free_flow(
            f"S-curve plot written to {Path(output_name).absolute()} "
            "(if matplotlib is installed). Press enter to continue: "
        )

    @staticmethod
    def extract_metrics():
        """Writes a CSV of quality metrics (RMSE, MAE, R2, max error and error
        percentiles) per atom/property for the selected models and validation
        set. Also prints the table to the screen."""

        if not _paths_are_valid():
            return

        output_name = model_analysis_menu_options.selected_metrics_output
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


# make menu items
model_analysis_menu_items = [
    FunctionItem(
        "Select models directory",
        ModelAnalysisFunctions.select_models_directory,
    ),
    FunctionItem(
        "Select validation/test set PointsDirectory",
        ModelAnalysisFunctions.select_validation_set_directory,
    ),
    FunctionItem(
        "Select property types (optional filter)",
        ModelAnalysisFunctions.select_property_types,
    ),
    FunctionItem(
        "Make S-curves (Excel workbook)",
        ModelAnalysisFunctions.make_s_curves_excel,
    ),
    FunctionItem(
        "Make S-curves (matplotlib image)",
        ModelAnalysisFunctions.make_s_curves_plot,
    ),
    FunctionItem(
        "Extract quality metrics (CSV)",
        ModelAnalysisFunctions.extract_metrics,
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
