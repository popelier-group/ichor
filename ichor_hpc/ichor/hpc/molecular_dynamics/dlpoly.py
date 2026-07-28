import shutil
from pathlib import Path
from typing import Optional, Union

import ichor.hpc.global_variables

from ichor.core.common.io import mkdir
from ichor.core.files import Trajectory
from ichor.core.files.dl_poly import (
    DlPolyConfig,
    DlPolyControl,
    DlPolyFFLUXInput,
    DlPolyField,
)
from ichor.core.models import Models
from ichor.hpc.batch_system.jobs import JobID
from ichor.hpc.submission_commands import DlpolyCommand
from ichor.hpc.submission_script import SubmissionScript


def write_dlpoly_fflux_setup(
    run_path: Union[str, Path],
    model_directory: Union[str, Path],
    starting_geometry: Union[str, Path],
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    electrostatics: str = "cluster",
    electrostatics_level: int = 3,
) -> Path:
    """Sets up a directory from which a DL_FFLUX (FFLUX-modified DL_POLY) calculation
    can be run. This writes out the DL_POLY input files (CONTROL, CONFIG, FIELD),
    the FFLUX.in settings file, and copies the trained model (``.model``) files into a
    ``model_krig`` subdirectory of the run directory.

    :param run_path: Directory in which to set up (and later run) the DL_FFLUX calculation.
        The directory is created if it does not exist.
    :param model_directory: Directory containing the trained models to use for the
        force field (usually one of the ``6_MODEL/xxx`` subfolders).
    :param starting_geometry: A ``.xyz`` file containing the starting geometry (geometries)
        which is written to the CONFIG file.
    :param ensemble: The DL_POLY ensemble to use, either ``"nvt"`` or ``"nve"``, defaults to ``"nvt"``.
    :param temperature: The temperature of the simulation, defaults to 1.
    :param timestep: The timestep (in ps) of the simulation, defaults to 0.001.
    :param nsteps: The number of timesteps to run the simulation for, defaults to 500.
    :param electrostatics: The electrostatics model written to FFLUX.in when the models
        contain multipole moment data, either ``"cluster"`` or ``"ewald"``, defaults to
        ``"cluster"``. Ignored when the models only contain ``iqa`` (energy) data.
    :param electrostatics_level: The multipole expansion level (L1-L5) for the
        electrostatics directive, defaults to 3. Ignored when there is no multipole data.
    :return: The path to the run directory which has been set up.
    """

    run_path = Path(run_path)
    mkdir(run_path)

    # read the starting geometry which is written to the CONFIG file. A DL_FFLUX run
    # starts from a single geometry (one molecule, matching the single-molecule FIELD
    # file), so if the provided xyz contains multiple geometries only the first is used.
    trajectory = Trajectory(starting_geometry)
    if len(trajectory) > 1:
        ichor.hpc.global_variables.LOGGER.warning(
            f"The starting geometry '{starting_geometry}' contains {len(trajectory)} "
            "geometries; only the first one will be used for the DL_FFLUX CONFIG file."
        )
    # a single-geometry trajectory so that CONFIG matches the FIELD file
    starting_trajectory = trajectory[0:1]
    atoms = trajectory[0]

    # the models define the chemical system name, which is used to label atoms in the
    # CONFIG file so that DL_FFLUX picks up the correct model file for each atom.
    models = Models(model_directory)
    # DL_FFLUX reconstructs each model's filename from the CONFIG atom label by inserting
    # the property (e.g. "iqa") as the SECOND "_"-delimited token, i.e. it assumes the
    # system name is a single token with no underscores. Model files whose system name
    # contains underscores (e.g. "BZAMID05_MOL_MTD_OUT0_iqa_O1.model") would be looked up
    # under the wrong name, so build an underscore-free system name and copy the models
    # under matching filenames (see the model copy below).
    first_tokens = models[0].path.stem.split("_")
    if len(first_tokens) >= 3:
        full_system_name = "_".join(first_tokens[:-2])
    else:
        full_system_name = models[0].system_name
    system_name = full_system_name.replace("_", "")

    # the electrostatics directive is only meaningful when the models contain multipole
    # moment data (anything other than the iqa energy). For iqa-only models it is omitted.
    has_multipole_data = any(prop != "iqa" for prop in models.types)

    # FFLUX-specific settings live in FFLUX.in, so the inline fflux directives are
    # omitted from the CONTROL file (fflux_cluster / fflux_print set to None)
    DlPolyControl(
        system_name=system_name,
        path=run_path / "CONTROL",
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        steps=nsteps,
        fflux_cluster=None,
        fflux_print=None,
    ).write()

    DlPolyConfig(
        system_name=system_name,
        trajectory=starting_trajectory,
        path=run_path / "CONFIG",
    ).write()

    DlPolyField(
        system_name=system_name,
        atoms=atoms,
        path=run_path / "FIELD",
    ).write()

    DlPolyFFLUXInput(
        path=run_path / "FFLUX.in",
        title=system_name,
        electrostatics=electrostatics if has_multipole_data else None,
        electrostatics_level=electrostatics_level,
    ).write()

    # copy the model files into a "model_krig" subdirectory (where DL_FFLUX looks for the
    # trained models), renaming them so the system part is the single underscore-free
    # token used in the CONFIG atom labels: <system_name>_<property>_<atom>.model
    model_krig_dir = run_path / "model_krig"
    mkdir(model_krig_dir)
    for model in models:
        tokens = model.path.stem.split("_")
        # filename layout is <system...>_<property>_<atom>.model
        prop, atom = tokens[-2], tokens[-1]
        new_name = f"{system_name}_{prop}_{atom}{model.path.suffix}"
        shutil.copy2(model.path, model_krig_dir / new_name)

    return run_path


def submit_dlpoly_fflux(
    run_path: Union[str, Path],
    model_directory: Union[str, Path],
    starting_geometry: Union[str, Path],
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    ncores: int = 1,
    electrostatics: str = "cluster",
    electrostatics_level: int = 3,
    executable_path: Optional[Union[str, Path]] = None,
) -> JobID:
    """Sets up and submits a DL_FFLUX (FFLUX-modified DL_POLY) calculation to a compute node.

    See :func:`write_dlpoly_fflux_setup` for a description of the setup arguments.

    :param ncores: The number of cores to use for the DL_FFLUX job, defaults to 1.
    :param executable_path: An optional path to the DL_FFLUX (DLPOLY.Z) executable which
        overrides the configured ``software.dlpoly.executable_path``. If ``None`` (default),
        the configured executable path is used.
    :return: An object containing information for the submitted job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    run_path = write_dlpoly_fflux_setup(
        run_path=run_path,
        model_directory=model_directory,
        starting_geometry=starting_geometry,
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        nsteps=nsteps,
        electrostatics=electrostatics,
        electrostatics_level=electrostatics_level,
    )

    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["dlpoly"], ncores=ncores
    ) as submission_script:
        submission_script.add_command(DlpolyCommand(executable_path, run_path))

    return submission_script.submit()


def submit_dlpoly_fflux_robustness(
    base_path: Union[str, Path],
    model_directory: Union[str, Path],
    seed_trajectory: Union[str, Path],
    nseeds: int,
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    ncores: int = 1,
    electrostatics: str = "cluster",
    electrostatics_level: int = 3,
    executable_path: Optional[Union[str, Path]] = None,
) -> JobID:
    """Sets up and submits a DL_FFLUX model-robustness check.

    A robustness check runs several independent DL_FFLUX simulations, each started from a
    different (diverse) seed geometry, to probe how stable the model is across the
    accessible configuration space (e.g. checking for the trajectory "exploding" or
    "imploding"). The first ``nseeds`` geometries are taken, in order, from the supplied
    (usually diversity-sampled) trajectory. Each seed gets its own ``RUN<i>`` directory
    under ``base_path``, and all runs are submitted together as a single job array.

    :param base_path: Base directory in which the per-seed ``RUN<i>`` directories are created.
    :param model_directory: Directory containing the trained models (e.g. a ``6_MODEL/xxx`` subfolder).
    :param seed_trajectory: A ``.xyz`` trajectory (usually the diversity-sampled set) from
        which the seed geometries are taken in order.
    :param nseeds: The number of seed geometries (and hence separate runs) to set up. If
        this exceeds the number of geometries available, all available geometries are used.
    :param ensemble: The DL_POLY ensemble to use, either ``"nvt"`` or ``"nve"``, defaults to ``"nvt"``.
    :param temperature: The temperature of the simulations, defaults to 1.
    :param timestep: The timestep (in ps) of the simulations, defaults to 0.001.
    :param nsteps: The number of timesteps to run each simulation for, defaults to 500.
    :param ncores: The number of cores to use per run, defaults to 1.
    :param electrostatics: The electrostatics model written to FFLUX.in when the models
        contain multipole moment data, defaults to ``"cluster"``.
    :param electrostatics_level: The multipole expansion level (L1-L5), defaults to 3.
    :param executable_path: An optional path to the DL_FFLUX (DLPOLY.Z) executable which
        overrides the configured ``software.dlpoly.executable_path``. If ``None`` (default),
        the configured executable path is used.
    :return: An object containing information for the submitted (array) job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    base_path = Path(base_path)
    mkdir(base_path)

    trajectory = Trajectory(seed_trajectory)
    # take the first nseeds geometries in order, but never more than are available
    nseeds = min(nseeds, len(trajectory))

    run_paths = []
    for i in range(nseeds):
        run_path = base_path / f"RUN{i}"
        mkdir(run_path)

        # materialise this seed geometry as an xyz inside the run directory, then
        # use the standard single-run setup to write CONTROL/CONFIG/FIELD/FFLUX.in
        seed_xyz = run_path / "seed.xyz"
        seed = Trajectory(seed_xyz)
        seed.add(trajectory[i])
        seed.write()

        write_dlpoly_fflux_setup(
            run_path=run_path,
            model_directory=model_directory,
            starting_geometry=seed_xyz,
            ensemble=ensemble,
            temperature=temperature,
            timestep=timestep,
            nsteps=nsteps,
            electrostatics=electrostatics,
            electrostatics_level=electrostatics_level,
        )
        run_paths.append(run_path)

    # add one DL_POLY command per run directory to a single submission script; ichor
    # groups these same-type commands into a job array (one array task per run)
    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["dlpoly"], ncores=ncores
    ) as submission_script:
        for run_path in run_paths:
            submission_script.add_command(DlpolyCommand(executable_path, run_path))

    return submission_script.submit()
