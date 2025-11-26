import shutil
from pathlib import Path
from typing import Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir
from ichor.core.files.polus import DatasetPrepScript, DiversityScript

from ichor.hpc.batch_system import JobID
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


def write_pyferebus_input_script(
    filename: Union[str, Path],
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    mkdir(ichor.hpc.global_variables.FILE_STRUCTURE["training_models"])
    output_dir = Path(ichor.hpc.global_variables.FILE_STRUCTURE["training_models"])
    input_filename = "pyferebus" + PyFerebusScript.get_filetype()
    input_file_path = Path(output_dir / input_filename)

    pyferebus_input_script = PyFerebusScript(
        Path(input_file_path),
        **kwargs,
    )
    pyferebus_input_script.write()

    return pyferebus_input_script.path


def submit_pyferebus(
    input_script: Path,
    script_name: Optional[Union[str, Path]],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> JobID:
    """Function that writes out a submission script which contains an array of
    Gaussian jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of
    all the .gjf file that need to be ran through Gaussian),
    and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes.
    However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
    the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param gjfs: A list of Path objects pointing to .gjf files
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
        even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold.
        This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        submission_script.add_command(PythonCommand(input_script))

    return submission_script.submit(hold=hold)
