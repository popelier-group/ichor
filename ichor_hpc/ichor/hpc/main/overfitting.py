from pathlib import Path
from typing import Optional

from ichor.hpc.batch_system import JobID
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)


def submit_overfitting_report(
    model_folder: Path,
    output_path: Path,
    set_type: str = "",
    ncores: int = 1,
    workers: Optional[int] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Submits the overfitting check of one folder of trained models to a compute node.

    The check is far heavier than the rest of the model analysis: it inverts the training
    covariance matrix of every model, which is cubic in the training set size on top of a
    covariance matrix that is quadratic in it, so a batch of a few hundred models runs for
    tens of minutes. That is not work for a login node, and the report is written to a
    file rather than read off the screen, so there is nothing lost by queueing it.

    Every model is independent of every other, so the job checks several of them at
    once (see the ``ncores`` argument of
    :func:`ichor.core.analysis.overfitting.overfitting_report`).

    :param model_folder: A folder holding the ``.model`` files to check. The held-out
        CSVs of the split are expected to be co-located under it, as the extract step
        writes them.
    :param output_path: Path the report CSV is written to. Its parent directory is made
        by the job itself, as the job runs on a compute node with nothing else to make
        it.
    :param set_type: Name of the held-out split whose CSVs are read, e.g.
        ``EXT_VALIDATION_SET``. If empty, no held-out CSVs are looked for and only the
        leave-one-out half of the check is reported.
    :param ncores: Number of cores the job asks for. The batch system hands out memory
        per core, so this is what the job's memory comes from as well as its cores.
    :param workers: Number of models the job checks at once. Defaults to one per core,
        which is the fastest. Pass fewer when one check needs more memory than one core
        brings, so that the job is still given the memory of all the cores while running
        only as many checks at a time as that memory holds.
    :param hold: An optional JobID to hold for. The check will not run until that other
        job has finished.
    :return: The JobID of the submitted job.
    """

    model_folder = Path(model_folder).absolute()
    output_path = Path(output_path).absolute()
    workers = max(1, workers or ncores)

    text_list = []
    # the python code the job runs, as `python -c` cannot take a for loop
    text_list.append("from pathlib import Path")
    text_list.append("from ichor.core.models import Models")
    text_list.append(
        "from ichor.core.analysis.overfitting import overfitting_report,"
        " summarise_diagnoses"
    )
    text_list.append(f"model_folder = Path('{model_folder}')")
    text_list.append(f"output_path = Path('{output_path}')")
    text_list.append("output_path.parent.mkdir(parents=True, exist_ok=True)")

    # without a split there is nothing to compare the leave-one-out figures against, so
    # the job is told to look for no CSVs at all rather than for a file name with an
    # empty split in it
    if set_type:
        text_list.append(f"csv_files = sorted(model_folder.rglob('*_{set_type}.csv'))")
    else:
        text_list.append("csv_files = []")

    text_list.append(
        "report = overfitting_report(Models(model_folder), csv_files_list=csv_files,"
        f" split_name='{set_type}', output_location=output_path, ncores={workers})"
    )
    # printed into the job's output file, so the outcome can be read without opening
    # the report itself
    text_list.append("print(summarise_diagnoses(report))")

    return submit_free_flow_python_command_on_compute(
        text_list,
        SCRIPT_NAMES["overfitting"],
        ncores=ncores,
        hold=hold,
    )
