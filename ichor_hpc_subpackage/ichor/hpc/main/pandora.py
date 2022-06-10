from pathlib import Path
from typing import List, Optional, Tuple

from ichor.core.common.io import cp
from ichor.core.files import (WFN, MorfiDirectory, PandoraDirectory,
                              PandoraInput, PointDirectory, PointsDirectory,
                              PySCFDirectory)
from ichor.hpc.batch_system import JobID
from ichor.hpc.log import logger
from ichor.hpc.submission_script import (SCRIPT_NAMES, MorfiCommand,
                                         PandoraPySCFCommand, SubmissionScript)


def submit_points_directory_to_pyscf(
    directory: Path, force: bool = False
) -> Optional[JobID]:
    """Function that submits all .gjf files in a directory to Gaussian, which will output .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    """
    points = PointsDirectory(
        directory
    )  # a directory which contains points (a bunch of molecular geometries)
    pandora_inputs = write_pandora_input(points)
    point_directories = [point.path for point in points]
    return submit_pandora_input_to_pyscf(
        pandora_inputs, point_directories, force=force
    )


def submit_pandora_input_to_pyscf(
    pandora_inputs: List[Path],
    point_directories: Optional[List[Path]] = None,
    force: bool = False,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    if point_directories is None:
        point_directories = [None for _ in range(len(pandora_inputs))]
    # make a SubmissionScript instance which is going to house all the jobs that are going to be ran
    with SubmissionScript(
        SCRIPT_NAMES["pandora"]["pyscf"]
    ) as submission_script:
        for pandora_input, point_directory in zip(
            pandora_inputs, point_directories
        ):
            if (
                force
                or not (
                    pandora_input.parent
                    / PandoraDirectory.dirname
                    / PySCFDirectory.dirname
                ).exists()
            ):
                submission_script.add_command(
                    PandoraPySCFCommand(pandora_input, point_directory)
                )
                logger.debug(
                    f"Adding {pandora_input} to {submission_script.path}"
                )  # make a list of GaussianCommand instances.
    # write the final submission script file that containing the job that needs to be ran (could be an array job that has many tasks)
    if len(submission_script.commands) > 0:
        logger.info(
            f"Submitting {len(submission_script.commands)} Pandora Input(s) to PySCF"
        )
        # submit the final submission script to the queuing system, so that job is ran on compute nodes.
        return submission_script.submit(hold=hold)


def write_pandora_input(points: PointsDirectory) -> List[Path]:
    pandora_inputs = []
    for point in points:
        if not point.pandora_input.exists():
            point.pandora_input = PandoraInput(
                point.path / f"{point.path.name}{PandoraInput.filetype}"
            )
            point.pandora_input.atoms = point.xyz.atoms
        point.pandora_input.write()
        pandora_inputs.append(point.pandora_input.path)
    return pandora_inputs


def copy_aimall_wfn_to_point_directory(
    pandora_directory: Path, point_directory: Path
) -> Optional[Path]:
    pandora_directory = PandoraDirectory(pandora_directory)
    point_directory = PointDirectory(point_directory)

    if pandora_directory.pyscf.exists():
        if pandora_directory.pyscf.aimall_wfn.exists():
            if not point_directory.exists():
                point_directory.mkdir()
            aimall_wfn = (
                point_directory.path
                / f"{point_directory.path.name}{WFN.filetype}"
            )
            cp(pandora_directory.pyscf.aimall_wfn.path, aimall_wfn)
            return aimall_wfn
        else:
            logger.error(
                f"Expected AIMAll WFN '{pandora_directory.pyscf.aimall_wfn.path}' does not exist"
            )
    else:
        logger.error(
            f"Expected Pandora PySCF Directory '{pandora_directory.pyscf.path}' does not exist"
        )


def submit_points_directory_to_morfi(
    directory: Path,
    atoms: Optional[List[str]] = None,
    force: bool = False,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    points = PointsDirectory(directory)
    morfi_inputs, aimall_wfns, point_directories = check_pyscf_wfns(points)
    return submit_morfi(
        morfi_inputs,
        aimall_wfns,
        point_directories,
        atoms=atoms,
        hold=hold,
        force=force,
    )


def submit_morfi(
    morfi_inputs: List[Path],
    aimall_wfns: Optional[List[Path]] = None,
    point_directories: Optional[List[Path]] = None,
    atoms: Optional[List[str]] = None,
    force: bool = False,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    if aimall_wfns is None:
        aimall_wfns = [None for _ in range(len(morfi_inputs))]
    if point_directories is None:
        point_directories = [None for _ in range(len(morfi_inputs))]
    with SubmissionScript(
        SCRIPT_NAMES["pandora"]["morfi"]
    ) as submission_script:
        for morfi_input, aimall_wfn, point_directory in zip(
            morfi_inputs, aimall_wfns, point_directories
        ):
            if (
                force
                or not (
                    morfi_input.parent
                    / PandoraDirectory.dirname
                    / MorfiDirectory.dirname
                ).exists()
            ):
                submission_script.add_command(
                    MorfiCommand(
                        morfi_input, aimall_wfn, point_directory, atoms=atoms
                    )
                )

    if len(submission_script.commands) > 0:
        return submission_script.submit(hold=hold)


def check_pyscf_wfns(
    points: PointsDirectory,
) -> Tuple[List[Path], List[Path], List[Path]]:
    morfi_inputs = []
    aimall_wfns = []
    point_directories = []
    for point in points:
        if point.pandora.exists() and point.pandora_input.exists():
            morfi_inputs.append(point.pandora_input.path)
            if (
                not point.wfn.exists()
                and point.pandora.pyscf.exists()
                and point.pandora.pyscf.aimall_wfn.exists()
            ):
                point.wfn = WFN(
                    copy_aimall_wfn_to_point_directory(
                        point.pandora.path, point.path
                    )
                )
            aimall_wfns.append(point.wfn.path)
            point_directories.append(point.path)

    return morfi_inputs, aimall_wfns, point_directories


def add_dispersion_to_aimall(point_directory: Path):
    point = PointDirectory(point_directory)
    point.read()
    dispersion_data = point.pandora.morfi.mout.interaction_energy
    for atom, int_ in point.ints.items():
        dispersion = dispersion_data[atom]
        int_.dispersion_data = {
            "dispersion": dispersion,
            # "iqa_dispersion": int_.iqa + dispersion,  # no longer needed
        }
        int_.write_json()
