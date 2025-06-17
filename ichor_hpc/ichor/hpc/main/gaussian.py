from pathlib import Path
import shutil
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.files import GJF, PointsDirectory, WFN
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import GaussianCommand
from ichor.hpc.submission_script import SubmissionScript
from ichor.core.common.io import mkdir

import traceback


def submit_single_gaussian_xyz(
    input_xyz_path: Union[str, Path],
    ncores=2,
    keywords="opt",
    method="b3lyp",
    basis_set="6-31+g(d,p)",
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    ichor.hpc.global_variables.LOGGER.info("Called fn for single gaussian job")
    input_xyz_path = Path(input_xyz_path)

    mkdir(ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"])
    ichor.hpc.global_variables.LOGGER.info("made folder for calc")

    opt_dir = ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"]

    shutil.copy(input_xyz_path, opt_dir)
    ichor.hpc.global_variables.LOGGER.info("copied file to dir")

    try:
        submit_points_directory_to_gaussian(
            points_directory=opt_dir,
            overwrite_existing=True,
            force_calculate_wfn=False,
            ncores=ncores,
            method=method,
            basis_set=basis_set,
            outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
            / input_xyz_path.name
            / "GAUSSIAN",
            errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
            / input_xyz_path.name
            / "GAUSSIAN",
        )
    except:
        with open("tb.txt", "w+") as f:
            traceback.print_exc(file=f)

    # write .gjf into folder
    # write submission script to submit job within folder


def submit_points_directory_to_gaussian(
    points_directory: Union[Path, PointsDirectory],
    overwrite_existing=False,
    force_calculate_wfn: bool = False,
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out .gjf files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .gjf files in a directory to Gaussian. Gaussian outputs .wfn files.

    :param directory: A Path object which is the path of the directory
        (commonly traning set path, sample pool path, etc.).
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
        even if .wfn files already exist. Defaults to False.
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written gjf files (overwriting
        settings from previously existing gjf files)
    """
    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    gjf_files = write_gjfs(points_directory, overwrite_existing, **kwargs)
    return submit_gjfs(
        gjf_files,
        script_name=script_name,
        force_calculate_wfn=force_calculate_wfn,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )


def write_gjfs(
    points_directory: PointsDirectory, overwrite_existing: bool, **kwargs
) -> List[Path]:
    """Writes out .gjf files in every PointDirectory which is contained
    in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the `.gjf`
    file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a
        whole directory containing points (such as TRAINING_SET).
    :return: A list of Path objects which point to `.gjf` files in each
        PointDirectory that is contained in the PointsDirectory.
    """

    gjfs = []

    for point_directory in points_directory:

        # remove the .pointdirectory suffix
        gjf_fle_name = point_directory.path.with_suffix("").name + GJF.get_filetype()

        # if overwriting, then delete current gjfs if they exist
        if overwrite_existing:
            # the gjf file object might not exist, so check for that first
            if point_directory.gjf:
                # if the object exists, then delete it
                point_directory.gjf.path.unlink()

            point_directory.gjf = GJF(
                Path(point_directory.path / gjf_fle_name),
                **kwargs,
            )
            point_directory.gjf.atoms = point_directory.xyz.atoms
            point_directory.gjf.write()

        # if gjf does not exist
        elif not point_directory.gjf:

            point_directory.gjf = GJF(
                Path(point_directory.path / gjf_fle_name),
                **kwargs,
            )
            point_directory.gjf.atoms = point_directory.xyz.atoms
            point_directory.gjf.write()

        gjfs.append(point_directory.gjf.path)

    return gjfs


def submit_gjfs(
    gjfs: List[Path],
    force_calculate_wfn: bool = False,
    script_name: Optional[Union[str, Path]] = ichor.hpc.global_variables.SCRIPT_NAMES[
        "gaussian"
    ],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
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

        number_of_jobs = 0

        for gjf in gjfs:

            # (even if wfn file exits) or a wfn file does not exist
            if force_calculate_wfn or not gjf.with_suffix(".wfn").exists():
                # make a list of GaussianCommand instances.
                submission_script.add_command(GaussianCommand(gjf))

                number_of_jobs += 1

            # case where the wfn file exists but does not have total energy
            # or something else is wrong with the file
            elif gjf.with_suffix(".wfn").exists():
                # make a list of GaussianCommand instances.
                try:
                    wfn_file = WFN(gjf.with_suffix(".wfn"))
                    wfn_file.read()  # file is being read here
                # if file is empty, then stopiteration should be raised
                # then add to list of files to run Gaussian on
                except StopIteration:

                    submission_script.add_command(GaussianCommand(gjf))
                    number_of_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Added {number_of_jobs} / {len(gjfs)} Gaussian jobs to {submission_script.path}"
        )

    # submit on compute node if there are files to submit
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} GJF(s) to Gaussian"
        )
        return submission_script.submit(hold=hold)
    else:
        raise ValueError("There are no jobs to submit in the submission script.")


# Below are functions used by autorun to check if stuff exists and reruns if necessary.

# def rerun_gaussian(gaussian_file: str):
#     """Used by `CheckManager`. Checks if Gaussian jobs ran correctly and a full .wfn
#     file is returned. If there is no .wfn file or it does not
#     have the correct contents, then rerun Gaussian.

#     :param gaussian_file: A string that is a Path to a .gjf file
#     """
#     if not gaussian_file:
#         print_completed()
#         sys.exit()
#     if Path(gaussian_file).with_suffix(".wfn").exists() and "TOTAL ENERGY" in last_line(
#         Path(gaussian_file).with_suffix(".wfn")
#     ):
#         print_completed()
#     else:
#         ichor.hpc.global_variables.logger.error(f"Gaussian Job {gaussian_file} failed to run")


# def scrub_gaussian(gaussian_file: str):
#     """Used by `CheckManager`. Checks if Gaussian job ran correctly.
#     If it did not, it will move the Point to the
#   `ichor.hpc.global_variables.FILE_STRUCTURE["gaussian_scrubbed_points"]` directory
#     and record that it has moved the point in the log file. If a .wfn file exists
#     and it contains the correct information in its last line, then
#     this checking function will not do anything.

#     :param gaussian_file: A string that is a Path to a .gjf file
#     """

#     gaussian_file = Path(gaussian_file)
#     point = PointDirectory(gaussian_file.parent)

#     reason: Optional[str] = None
#     if not gaussian_file.exists():
#         reason = f"{gaussian_file} does not exist"
#     elif not point.wfn.exists():
#         reason = f"No WFN file found in directory {point.path}"
#     elif "TOTAL ENERGY" not in last_line(point.wfn.path):
#         reason = f"Incomplete WFN ('{point.wfn.path}') file found"

#     if reason is not None:
#         ichor.hpc.global_variables.logger.error(f"'{point.path}' will be ignored | Reason: {reason}")
#         point.ignore(reason)
