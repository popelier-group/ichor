import shutil
from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir

from ichor.core.files import PointsDirectory, XTB, XYZ
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_single_ase_xyz(
    input_xyz_path: Union[str, Path],
    ncores=2,
    method="GFN2-xT",
    solvent="none",
    electronic_temperature=300,
    max_iterations=2048,
    fmax=0.01,
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    input_xyz_path = Path(input_xyz_path)
    mkdir(ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"])
    opt_dir = ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"]
    shutil.copy(input_xyz_path, opt_dir)

    submit_points_directory_to_ase(
        points_directory=opt_dir,
        ncores=ncores,
        method=method,
        solvent=solvent,
        electronic_temperature=electronic_temperature,
        max_iterations=max_iterations,
        fmax=fmax,
        hold=hold,
        outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        / input_xyz_path.name
        / "ASE",
        errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
        / input_xyz_path.name
        / "ASE",
    )


def submit_points_directory_to_ase(
    points_directory: Union[Path, PointsDirectory],
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out XTB input files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .gjf files in a directory to Gaussian. Gaussian outputs .wfn files.

    :param directory: A Path object which is the path of the directory
        (commonly traning set path, sample pool path, etc.).
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written gjf files (overwriting
        settings from previously existing gjf files)
    """
    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    xtb_files = write_xtb_input(points_directory, **kwargs)
    return submit_xtb(
        xtb_files,
        script_name=script_name,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )


def write_xtb_input(
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


def submit_xtb(
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
