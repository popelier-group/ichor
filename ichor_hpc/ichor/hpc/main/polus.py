import shutil
from pathlib import Path
from typing import Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir, copytree
from ichor.core.files.polus import DatasetPrepScript, DiversityScript

from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


def write_diversity_sampling(
    filename: Union[str, Path],
    seed_geom: Union[str, Path],
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    # diversity parent folder
    div_parent = Path(ichor.hpc.global_variables.FILE_STRUCTURE["diversity_sampling"])
    mkdir(div_parent)
    # extract system name from traj
    system_name_long = Path(filename).stem
    system_name_str = system_name_long.replace("_MTD_OUT", "")
    system_name = system_name_str.replace("_mtd_out", "")
    # subfolder for running calc
    output_dir = Path(div_parent / system_name)
    mkdir(output_dir)

    # make python script within subfolder
    input_filename = "diversity_input" + DiversityScript.get_filetype()
    input_file_path = Path(output_dir / input_filename)

    div_input_script = DiversityScript(
        Path(input_file_path),
        seed_geom=seed_geom,
        output_dir=output_dir,
        filename=filename,
        system_name=system_name,
        **kwargs,
    )
    div_input_script.write()

    return div_input_script.path


def write_dataset_prep(
    outlier_input_dir: Union[Path, str],
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    # extract system name from data somehow...
    system_name = Path(outlier_input_dir).parent.name.split(".", 1)[0]

    # Make new parent directory called DATASETS
    data_parent = ichor.hpc.global_variables.FILE_STRUCTURE["training"]
    mkdir(data_parent)
    # Make a subfolder for the structure
    dataset_dir = Path(data_parent / system_name)
    mkdir(dataset_dir)
    # Move input files dir into DATASETS dir
    # Make a subfolder for the processed CSVs
    csvs_string = "processed_csvs"
    src = Path(outlier_input_dir)
    dst = dataset_dir / csvs_string
    mkdir(dst)
    # copy to avoid accidental deletion
    copytree(src, dst)

    input_filename = "dataset_split" + DatasetPrepScript.get_filetype()
    input_file_path = Path(dataset_dir / input_filename)

    dataset_input_script = DatasetPrepScript(
        Path(input_file_path),
        outlier_input_dir=csvs_string,
        system_name=system_name,
        **kwargs,
    )
    dataset_input_script.write()

    return input_filename, dataset_dir


def submit_polus(
    input_script: Path,
    script_name: Optional[Union[str, Path]],
    cwd: Optional[Path] = None,
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
        cwd=cwd or Path.cwd(),
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        submission_script.add_command(PythonCommand(input_script))

    return submission_script.submit(hold=hold)
