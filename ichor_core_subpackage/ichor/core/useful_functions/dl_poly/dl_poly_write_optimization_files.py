def write_control(
    system_name: str,
    ensemble: str = "nvt",
    thermostat: str = "hoover",
    hoover_number: float = 0.04,
    temperature: int = 1,
    timestep: float = 0.001,
    n_steps: int = 500,
    file_name: str = "CONTROL",
):
    """Writes CONTROL file that DL_FFLUX needs to function. It is a modified version of the DL_POLY CONTROL file.
    The defaults of the function are used to perform a geometry optimization, so the settings are different
    that the default settings.

    :param system_name: The name of the system
    :parm ensemble: The ensemble to use for the simulation, defaults to nvt
    :param thermostat: The thermostat to use for the simulation, defaults to hoover (Nose-Hoover thermostat)
    :param hoover_number: The relaxation constant of Nose-Hoover thermostat in ps, defaults to 0.04
    :param temperature: The temperature to run the simulation at, defaults to 0.0 (note that simulation is actually ran at 10K)
        because `zero` keyword is also added.
    :param timestep: The timestep time, defaults to 0.001 ps
    :param n_steps: The number of timesteps for the simulation, defaults to 500
    """
    # have import in function to prevent cyclic imports
    from ichor.core.files.dl_poly import DlPolyControl

    control_file = DlPolyControl(
        path=file_name,
        system_name=system_name,
        ensemble=ensemble,
        thermostat=thermostat,
        thermostat_settings=[hoover_number],
        temperature=temperature,
        timestep=timestep,
        n_steps=n_steps,
    )
    control_file.write()


def write_config(
    atoms: "Atoms", system_name: str, cell_size: float = 50.0, file_name: str = "CONFIG"
):
    """Writes CONFIG file that DL_FFLUX needs to run.

    :param atoms: An Atoms instance that is the starting geometry of the DL_FFLUX MD simulation
    :param cell_size: The box size. Default is 50x50x50 Angstroms. Can be a cube only.
    :param system_name: The system name
    :parm file_name: The name of the config file. It has to be `CONFIG` to be read in correctly by DL_FFLUX.
    """
    # have import in function to prevent cyclic imports
    from ichor.core.files.dl_poly import DlPolyConfig

    dl_poly_config = DlPolyConfig(
        path=file_name, system_name=system_name, atoms=atoms, cell_size=cell_size
    )
    dl_poly_config.write()


def write_field(atoms: "Atoms", system_name: str, file_name="FIELD"):
    """Writes out DL FFLUX FIELD file.

    :param atoms: An Atoms instance which contains a geometry of the chemical system of interest.
    :param system_name: The name of the system
    :param file_name: The FIELD file name, defaults to "FIELD"
    """

    # have import in function to prevent cyclic imports
    from ichor.core.files.dl_poly import DlPolyField

    field_file = DlPolyField(path=file_name, atoms=atoms, system_name=system_name)
    field_file.write()
