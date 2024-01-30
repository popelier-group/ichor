from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.files import OrcaInput, PointsDirectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import OrcaCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_points_directory_to_orca(
    points_directory: Union[Path, PointsDirectory],
    overwrite_existing=False,
    force_calculate_wfn: bool = False,
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["orca"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out .inp files from .xyz files that are in each directory and
    submits ORCA jobs to compute nodes.

    :param directory: A Path object which is the path of the directory
        (commonly training set path, sample pool path, etc.).
    :param force_calculate_wfn: Run ORCA calculations on given input files,
        even if .wfn files already exist. Defaults to False.
    :param kwargs: Key word arguments to pass to orca input file class.
        These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written input files (overwriting
        settings from previously existing input files)
    """
    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    orca_files = write_orca_inputs(points_directory, overwrite_existing, **kwargs)
    return submit_orca_to_compute(
        orca_files,
        script_name=script_name,
        force_calculate_wfn=force_calculate_wfn,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )


def write_orca_inputs(
    points_directory: PointsDirectory, overwrite_existing: bool, **kwargs
) -> List[Path]:
    """Writes out .inp files in every PointDirectory which is contained
    in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the orca input
    file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a
        whole directory containing points (such as TRAINING_SET).
    :return: A list of Path objects which point to orca input files in each
        PointDirectory that is contained in the PointsDirectory.
    """

    orca_inputs = []

    for point_directory in points_directory:

        orca_file_name = point_directory.path.with_suffix("").name + OrcaInput.filetype

        if overwrite_existing:
            if point_directory.orca_input:
                point_directory.orca_input.path.unlink()

            point_directory.orca_input = OrcaInput(
                Path(point_directory.path / orca_file_name),
                **kwargs,
            )
            point_directory.orca_input.atoms = point_directory.xyz.atoms
            point_directory.orca_input.write()

        elif not point_directory.orca_input:

            point_directory.orca_input = OrcaInput(
                Path(point_directory.path / orca_file_name),
                **kwargs,
            )
            point_directory.orca_input.atoms = point_directory.xyz.atoms
            point_directory.orca_input.write()

        orca_inputs.append(point_directory.orca_input.path)

    return orca_inputs


def submit_orca_to_compute(
    orca_inputs: List[Path],
    force_calculate_wfn: bool = False,
    script_name: Optional[Union[str, Path]] = ichor.hpc.global_variables.SCRIPT_NAMES[
        "orca"
    ],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
) -> JobID:
    """Function that writes out a submission script which contains an array of
    ORCA jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of
    all the .orcainput file that need to be ran through ORCA),
    and it will submit the submission script to compute nodes as well to run ORCA on compute nodes.
    However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
    the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param orca_inputs: A list of Path objects pointing to ORCA .inp files
    :param force_calculate_wfn: Run ORCA calculation on the given files,
        even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to ichor.hpc.global_variables.SCRIPT_NAMES["orca"]
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

        number_of_jobs = 0

        for orca_input in orca_inputs:
            if force_calculate_wfn or not orca_input.with_suffix(".wfn").exists():
                submission_script.add_command(OrcaCommand(orca_input))

                number_of_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Added {number_of_jobs} / {len(orca_inputs)} ORCA jobs to {submission_script.path}"
        )

    # submit on compute node if there are files to submit
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} ORCA jobs"
        )
        return submission_script.submit(hold=hold)
    else:
        raise ValueError("There are no jobs to submit in the submission script.")
