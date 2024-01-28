from enum import Enum
from pathlib import Path
from typing import Union

import numpy as np
from ichor.core.files.file import FileContents, ReadFile, WriteFile


class AmberThermostat(Enum):
    ConstantEnergy = 0
    ConstantTemperature = 1
    Andersen = 2
    Langevin = 3
    OptimisedIsokineticNoseHoover = 9
    StochasticIsokineticNoseHoover = 10


class BondLengthConstraint(Enum):
    NoConstraint = 1  # SHAKE is not performed
    HydrogenBonds = 2  # bonds involving hydrogen are constrained
    AllBonds = 3  # all bonds are constrained (not available for parallel or qmmm runs in sander)


class ForceEvaluation(Enum):
    Complete = 1  # complete interaction is calculated
    OmitHBonds = 2  # bond interactions involving H-atoms omitted
    OmitBonds = 3  # all the bond interactions are omitted
    OmitHAngle = 4  # angle involving H-atoms and all bonds are omitted
    OmitAngle = 5  # all bond and angle interactions are omitted
    OmitHDihedral = 6  # dihedrals involving H-atoms and all bonds and all angle interactions are omitted
    OmitDihedral = 7  # all bond, angle and dihedral interactions are omitted
    OmitAll = 8  # all bond, angle, dihedral and non-bonded interactions are omitted


class PeriodicBoundaryCondition(Enum):
    NoPeriodicBoundary = 0  # no periodicity is applied and PME is off
    ConstantVolume = 1  # constant volume
    ConstantPressure = 2  # constant pressure


class AmberMDIn(WriteFile, ReadFile):
    """Class that handles amber input files `mdin`.d

    :param mdin_file: File where to write data
    :param nsteps: Number of timesteps to run simulation for
    :param dt: Timestep time in picoseconds, default is 0.001
    :param temperature: Temperature to perform simulation at, default is 300
    :param force_evaluation: _description_, defaults to ForceEvaluation.Complete
    :param bond_constraint: _description_, defaults to BondLengthConstraint.NoConstraint
    :param write_coordinates_every: Write coordinates every nth timestep, defaults to 1
    :param write_velocities_every: Write velocities out to mdcrd even nth step
        Note that these should not be written out as output format `ioutfm` is set to 0
        (meaning output is not in binary format), optional
    :param write_forces_every: Write atomic forces out to mdcrd every nth step
        Note that output file is not NETCDF (binary format), defaults to -1
    :param periodic_boundary_condition: Whether to use periodic boundary conditions or not,
        defaults to PeriodicBoundaryCondition.NoPeriodicBoundary
    :param thermostat: The thermostat to use for the simulation, defaults to AmberThermostat.Langevin
    :param ln_gamma: The collision frequency in picoseconds, defaults to 0.5
    """

    filetype = ".in"

    def __init__(
        self,
        path: Path,
        nsteps: int = FileContents,
        dt: float = FileContents,
        temperature: int = FileContents,
        force_evaluation: ForceEvaluation = FileContents,
        bond_constraint: BondLengthConstraint = FileContents,
        write_coordinates_every: int = FileContents,
        write_velocities_every: int = FileContents,  # if set to -1, then cannot write an ASCII file
        write_forces_every: int = FileContents,  # if set to -1, then cannot write an ASCII file
        periodic_boundary_condition: PeriodicBoundaryCondition = FileContents,
        thermostat: AmberThermostat = FileContents,
        ln_gamma: float = FileContents,
    ):
        super(ReadFile, self).__init__(path)

        self.nsteps = nsteps
        self.dt = dt
        self.temperature = temperature
        self.force_evaluation = force_evaluation
        self.bond_constraint = bond_constraint
        self.write_coordinates_every = write_coordinates_every
        self.write_velocities_every = write_velocities_every
        self.write_forces_every = write_forces_every
        self.periodic_boundary_condition = periodic_boundary_condition
        self.thermostat = thermostat
        self.ln_gamma = ln_gamma

    def __set_write_defaults_if_needed(self):
        """
        See class `WriteFile` this is called prior to writing file to set defautls
        """

        self.nsteps = self.nsteps or 100
        self.dt = self.dt or 0.001
        self.temperature = self.temperature or 300
        self.force_evaluation = self.force_evaluation or ForceEvaluation.Complete
        self.bond_constraint = self.bond_constraint or BondLengthConstraint.NoConstraint
        self.write_coordinates_every = self.write_coordinates_every or 1
        self.write_velocities_every = self.write_velocities_every or 0
        self.write_forces_every = self.write_forces_every or 0
        self.periodic_boundary_condition = (
            self.periodic_boundary_condition
            or PeriodicBoundaryCondition.NoPeriodicBoundary
        )
        self.thermostat = self.thermostat or AmberThermostat.Langevin
        self.ln_gamma = self.ln_gamma or 0.5

    def _read_file(self, *args, **kwargs):
        with open(self.path, "r") as f:
            for line in f:
                line = line.replace(",", "").strip()
                if "nstlim" in line:
                    self.nsteps = int(line.split("=")[-1])
                elif "dt" in line:
                    self.dt = float(line.split("=")[-1])
                elif "ntf" in line:
                    self.force_evaluation = ForceEvaluation(int(line.split("=")[-1]))
                elif "ntc" in line:
                    self.bond_constraint = BondLengthConstraint(
                        int(line.split("=")[-1])
                    )
                elif "temp0" in line:
                    self.temperature = int(line.split("=")[-1])
                elif "ntwx" in line:
                    self.write_coordinates_every = int(line.split("=")[-1])
                elif "ntwv" in line:
                    self.write_velocities_every = int(line.split("=")[-1])
                elif "ntwf" in line:
                    self.write_forces_every = int(line.split("=")[-1])
                elif "ntb" in line:
                    self.periodic_boundary_condition = PeriodicBoundaryCondition(
                        int(line.split("=")[-1])
                    )
                elif "ntt" in line:
                    self.thermostat = AmberThermostat(int(line.split("=")[-1]))
                elif "gamma_ln" in line:
                    self.ln_gamma = float(line.split("=")[-1])

    def _write_file(self, path: Path):
        with open(path, "w") as f:
            f.write("Production\n")
            f.write(" &cntrl\n")
            f.write("  imin=0,\n")  # not running minimisation
            f.write("  ntx=1,\n")  # read input coordinates only
            f.write("  irest=0,\n")  # not restarting simulation
            f.write(f"  nstlim={self.nsteps},\n")  # number of time steps
            f.write(f"  dt={self.dt},\n")  # time step in picoseconds
            f.write(f"  ntf={self.force_evaluation.value},\n")  # force constraint
            f.write(f"  ntc={self.bond_constraint.value},\n")  # bond contraint
            f.write(f"  temp0={self.temperature},\n")  # temperature
            f.write("  ntpr=1,\n")  # energy info printed to mdout every ntpr steps
            # coordinate info printed to mdout every ntwx steps
            f.write(f"  ntwx={self.write_coordinates_every},\n")
            # velocity info printed to mdout every ntwv steps
            f.write(f"  ntwv={self.write_velocities_every},\n")
            # force info printed to mdout every ntwf steps
            f.write(f"  ntwf={self.write_forces_every},\n")
            # output formatting, setting to 0 means that a human readable
            # file is written (not a NETCDF format which is binary)
            f.write("  ioutfm=0,\n")
            f.write("  cut=999.0,\n")  # nonbonded cutoff
            f.write(
                f"  ntb={self.periodic_boundary_condition.value},\n"
            )  # periodic boundary conditions
            f.write("  ntp=0,\n")  # pressure control
            f.write(f"  ntt={self.thermostat.value},\n")  # thermostat
            f.write(
                f"  gamma_ln={self.ln_gamma},\n"
            )  # ln(gamma) for the langevin thermostat
            f.write("  tempi=0.0,\n")  # temperature to initialise velocities
            f.write("  ig=-1\n")  # random seed (-1 randomises seed)
            f.write(" /\n")


def write_mdin(
    mdin_file: Path,
    nsteps: int,
    dt: float = 0.001,
    temperature: int = 300,
    force_evaluation: ForceEvaluation = ForceEvaluation.Complete,
    bond_constraint: BondLengthConstraint = BondLengthConstraint.NoConstraint,
    write_coordinates_every: int = 1,
    write_velocities_every: int = 0,
    write_forces_every: int = 0,
    periodic_boundary_condition: PeriodicBoundaryCondition = PeriodicBoundaryCondition.NoPeriodicBoundary,
    thermostat: AmberThermostat = AmberThermostat.Langevin,
    ln_gamma: float = 0.5,
):
    """Writes an AMBER md.in file with the given settings

    :param mdin_file: File where to write data
    :param nsteps: Number of timesteps to run simulation for
    :param dt: Timestep time in picoseconds, default is 0.001
    :param temperature: Temperature to perform simulation at, default is 300
    :param force_evaluation: _description_, defaults to ForceEvaluation.Complete
    :param bond_constraint: _description_, defaults to BondLengthConstraint.NoConstraint
    :param write_coordinates_every: Write coordinates every nth timestep, defaults to 1
    :param write_velocities_every: Write velocities out to mdcrd even nth step
        Note that these should not be written out as output format `ioutfm`
        is set to 0 (meaning output is not in binary format), optional
    :param write_forces_every: Write atomic forces out to mdcrd every nth step
        Note that output file is not NETCDF (binary format), defaults to -1
    :param periodic_boundary_condition: Whether to use periodic boundary conditions or not,
        defaults to PeriodicBoundaryCondition.NoPeriodicBoundary
    :param thermostat: The thermostat to use for the simulation, defaults to AmberThermostat.Langevin
    :param ln_gamma: The collision frequency in picoseconds, defaults to 0.5
    """

    AmberMDIn(
        mdin_file,
        nsteps,
        dt,
        temperature,
        force_evaluation,
        bond_constraint,
        write_coordinates_every,
        write_velocities_every,
        write_forces_every,
        periodic_boundary_condition,
        thermostat,
        ln_gamma,
    ).write()


def mdcrd_to_xyz(
    mdcrd: Union[str, Path],  # contains geometry
    prmtop: Union[str, Path],  # contains atom names
    mdin: Union[str, Path],  # contains temperature information
    system_name: str,
    every: int = 1,
):
    atom_names = []

    # read in atom names
    with open(prmtop, "r") as f:
        for line in f:
            if "ATOM_NAME" in line:
                _ = next(f)
                line = next(f)
                while "CHARGE" not in line:
                    atom_names += [a[0] for a in line.split()]
                    line = next(f)

    mdin_inst = AmberMDIn(mdin)

    temperature = ""
    if mdin_inst.exists():
        temperature = mdin_inst.temperature

    output_f_name = Path(f"{system_name}-amber{temperature}K.xyz")

    natoms = len(atom_names)
    with open(mdcrd, "r") as f:
        _ = next(f)
        traj = np.array([])
        i = 0
        with open(output_f_name, "w") as o:
            for line in f:
                traj = np.hstack((traj, np.array(line.split(), dtype=float)))
                if len(traj) == natoms * 3:
                    if i % every == 0:
                        traj = traj.reshape(natoms, 3)
                        o.write(f"{natoms}\n{i}\n")
                        for atom_name, atom in zip(atom_names, traj):
                            o.write(
                                f"{atom_name} {atom[0]:16.8f} {atom[1]:16.8f} {atom[2]:16.8f}\n"
                            )
                    i += 1
                    traj = np.array([])
