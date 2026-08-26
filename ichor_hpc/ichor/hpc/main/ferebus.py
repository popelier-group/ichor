import shutil
from pathlib import Path
from typing import Optional

import ichor.hpc.global_variables

from ichor.core.files.ferebus import ExtractModelsScript, PyFerebusScript
from ichor.hpc.batch_system import JobID
from tqdm import tqdm


def _training_dir_sort_key(training_dir: Path):
    """Sorts TRAIN folders by the training set size in their name, e.g. ``TRAIN-25``
    before ``TRAIN-1000``. A folder whose name holds no number is sorted first and by
    name, so that it cannot break the sort of the folders which do."""

    digits = "".join(filter(str.isdigit, training_dir.name))

    return (int(digits) if digits else 0, training_dir.name)


def find_and_setup_ferebus_subdirs(input_dir):
    # find directories containing training data and job-details files
    # makes sure to copy job-details file into each subdirectory
    # ferebus needs job-details and properties to be in same directory
    base = Path(input_dir)

    dest_paths = []

    # Recursively find TRAIN directories anywhere under base. Walking the tree is the
    # slow part (a dataset directory on a shared filesystem holds a lot of files), so it
    # is done under a progress bar: without one the menu looks like it has hung. How
    # many TRAIN folders there are is not known until the walk is over, so the bar
    # counts the paths looked at rather than showing a percentage.
    training_dirs = [
        d
        for d in tqdm(
            base.rglob("*"), desc="Searching for training sets", unit=" paths"
        )
        if d.is_dir() and "TRAIN" in d.name
    ]

    # sort numerically by the number in the folder name
    training_dirs.sort(key=_training_dir_sort_key)

    print(f"Found {len(training_dirs)} TRAIN directories.")

    # the copying below is quick next to the search above, but it is shown as a bar as
    # well so that the search bar is not left on screen looking like it is still running
    for d in tqdm(training_dirs, desc="Setting up training sets", unit=" set"):
        job_file = d / "job-details"
        if not job_file.is_file():
            # tqdm.write rather than print, so that the message does not land on top of
            # the progress bar
            tqdm.write(f"Skipping {d.name}: no job-details file")
            continue

        # exactly one subfolder inside each TRAIN directory
        subdirs = [p for p in d.iterdir() if p.is_dir()]
        if len(subdirs) != 1:
            tqdm.write(f"Skipping {d.name}: expected 1 subfolder, found {len(subdirs)}")
            continue

        dest = subdirs[0] / "job-details"
        shutil.copy(job_file, dest)

        dest_paths.append(dest)
        tqdm.write(f"Copied job-details -> {dest}")

    # return list of training directories so user can choose how many to submit
    return dest_paths


def pyferebus_platform() -> Optional[str]:
    """Returns the platform to set a pyferebus job up for, which is the machine
    ichor is running on. pyferebus writes its own submission script, so the name it
    is given is what decides which batch system that script is written for.

    The name is the key of the machine in the ichor config, upper cased, as that is
    the form pyferebus takes it in (e.g. ``csf3`` in the config is ``CSF3`` here).
    None is returned when the machine ichor is running on is not in the config, in
    which case the writer falls back to its own default.
    """

    machine = ichor.hpc.global_variables.MACHINE

    return machine.upper() if machine else None


def write_pyferebus_input_script(
    input_dir,
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    # the machine ichor is running on, unless the caller names the platform
    # itself. Without this every script is written for the platform the writer
    # defaults to, whichever machine it was written on.
    kwargs.setdefault("platform", pyferebus_platform())

    input_filename = "pyferebus_input" + PyFerebusScript.get_filetype()

    pyferebus_input_script = PyFerebusScript(
        Path(input_filename),
        **kwargs,
    )
    pyferebus_input_script.write()

    return pyferebus_input_script.path


def write_extract_models_script(
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    input_filename = "extract_models" + ExtractModelsScript.get_filetype()

    extract_models_script = ExtractModelsScript(
        Path(input_filename),
    )
    extract_models_script.write()

    return extract_models_script.path


# def submit_pyferebus(
#     input_script: Path,
#     script_name: Optional[Union[str, Path]],
#     hold: Optional[JobID] = None,
#     ncores=2,
#     outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
#     errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
#     **kwargs,
# ) -> JobID:
#     """Function that writes out a submission script which contains an array of
#     Gaussian jobs to be ran on compute nodes. If calling this function from
#     a log-in node, it will write out the submission script, a datafile (file which contains the names of
#     all the .gjf file that need to be ran through Gaussian),
#     and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes.
#     However, if using this function from a compute node,
#     (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
#     the datafile and will not submit any new jobs
#     from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

#     :param gjfs: A list of Path objects pointing to .gjf files
#     :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
#         even if .wfn files already exist. Defaults to False.
#     :script_name: Path to write submission script out to defaults to ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"]
#     :param hold: An optional JobID for which this job to hold.
#         This is used in auto-run to hold this job for the previous job to finish, defaults to None
#     :return: The JobID of this job given by the submission system.
#     """

#     # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
#     # the submission_script object can be accessed even after the context manager
#     with SubmissionScript(
#         script_name,
#         ncores=ncores,
#         outputs_dir_path=outputs_dir_path,
#         errors_dir_path=errors_dir_path,
#     ) as submission_script:

#         submission_script.add_command(PythonCommand(input_script))

#     return submission_script.submit(hold=hold)
