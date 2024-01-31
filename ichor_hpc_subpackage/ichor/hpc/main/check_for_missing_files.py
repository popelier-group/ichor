from pathlib import Path
from typing import Union

from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)


def submit_check_points_directory_for_missing_files(points_dir_path: Union[str, Path]):
    """Submits a job that checks if contents of files are present. Files are going to
    be written to the file which contains standard output from the job.

    :param points_dir_path: Path or PointsDirectory or PointsDirectoryParent-like directory
    """

    points_dir_path = Path(points_dir_path)

    is_parent_directory_to_many_points_directories = single_or_many_points_directories(
        points_dir_path
    )

    if is_parent_directory_to_many_points_directories:
        cls_to_use = "PointsDirectoryParent"
    else:
        cls_to_use = "PointsDirectory"

    text_list = []
    # make the python command that will be written in the submit script
    # it will get executed as `python -c python_code_to_execute...`
    text_list.append(f"from ichor.core.files import {cls_to_use}")
    text_list.append(
        "from ichor.core.processing.check_functions import check_gaussian_and_aimall"
    )
    # can use the processed data attribute because any function that works on a single
    # PointDirectory can be passed inside here.
    text_list.append(
        f"{cls_to_use}('{points_dir_path.absolute()}').processed_data(check_gaussian_and_aimall)"
    )

    return submit_free_flow_python_command_on_compute(
        text_list, SCRIPT_NAMES["check_for_missing_data"], ncores=1
    )
