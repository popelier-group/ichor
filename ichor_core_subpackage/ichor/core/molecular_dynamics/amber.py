from enum import Enum
from pathlib import Path
from typing import Optional, Union

import numpy as np
from ichor.core.common.functools import classproperty
from ichor.core.files.file import File, FileContents, ReadFile, WriteFile
from ichor.core.files.optional_file import OptionalFile


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
    OmitAll = (
        8  # all bond, angle, dihedral and non-bonded interactions are omitted
    )


class PeriodicBoundaryCondition(Enum):
    NoPeriodicBoundary = 0  # no periodicity is applied and PME is off
    ConstantVolume = 1  # constant volume
    ConstantPressure = 2  # constant pressure


class AmberMDIn(WriteFile, ReadFile):
    def __init__(
        self,
        path: Path,
        nsteps: Optional[int] = None,
        dt: float = 0.001,
        temperature: float = 300.0,
        force_evaluation: ForceEvaluation = ForceEvaluation.Complete,
        bond_constraint: BondLengthConstraint = BondLengthConstraint.NoConstraint,
        write_coordinates_every: int = 1,
        write_velocities_every: int = 0, # if set to -1, then cannot write an ASCII file
        write_forces_every: int = 0, # if set to -1, then cannot write an ASCII file
        periodic_boundary_condition: PeriodicBoundaryCondition = PeriodicBoundaryCondition.NoPeriodicBoundary,
        thermostat: AmberThermostat = AmberThermostat.Langevin,
        ln_gamma: float = 0.5,
    ):
        super(ReadFile, self).__init__(path)

        self.nsteps: int = FileContents

        self.nsteps: int = nsteps or FileContents
        self.dt: float = dt
        self.temperature: float = temperature
        self.force_evaluation: ForceEvaluation = force_evaluation
        self.bond_constraint: BondLengthConstraint = bond_constraint
        self.write_coordinates_every: int = write_coordinates_every
        self.write_velocities_every: int = write_velocities_every
        self.write_forces_every: int = write_forces_every
        self.periodic_boundary_condition: PeriodicBoundaryCondition = (
            periodic_boundary_condition
        )
        self.thermostat: AmberThermostat = thermostat
        self.ln_gamma: float = ln_gamma

    @classproperty
    def filetype(self) -> str:
        return ".in"

    def _initialise_contents(self):
        self.nsteps = self.nsteps or 0

    def _read_file(self, *args, **kwargs):
        with open(self.path, "r") as f:
            for line in f:
                line = line.replace(",", "")
                if "nstlim" in line:
                    self.nsteps = int(line.split("=")[-1])
                elif "dt" in line:
                    self.dt = float(line.split("=")[-1])
                elif "ntf" in line:
                    self.force_evaluation = ForceEvaluation(
                        line.split("=")[-1]
                    )
                elif "ntc" in line:
                    self.bond_constraint = BondLengthConstraint(
                        line.split("=")[-1]
                    )
                elif "temp0" in line:
                    self.temperature = float(line.split("=")[-1])
                elif "ntwx" in line:
                    self.write_coordinates_every = int(line.split("=")[-1])
                elif "ntwv" in line:
                    self.write_velocities_every = int(line.split("=")[-1])
                elif "ntwf" in line:
                    self.write_forces_every = int(line.split("=")[-1])
                elif "ntb" in line:
                    self.periodic_boundary_condition = (
                        PeriodicBoundaryCondition(line.split("=")[-1])
                    )
                elif "ntt" in line:
                    self.thermostat = AmberThermostat(line.split("=")[-1])
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
            f.write(
                f"  ntf={self.force_evaluation.value},\n"
            )  # force constraint
            f.write(f"  ntc={self.bond_constraint.value},\n")  # bond contraint
            f.write(f"  temp0={self.temperature},\n")  # temperature
            f.write(
                "  ntpr=1,\n"
            )  # energy info printed to mdout every ntpr steps
            f.write(
                f"  ntwx={self.write_coordinates_every},\n"
            )  # coordinate info printed to mdout every ntwx steps
            f.write(
                f"  ntwv={self.write_velocities_every},\n"
            )  # velocity info printed to mdout every ntwv steps
            f.write(
                f"  ntwf={self.write_forces_every},\n"
            )  # force info printed to mdout every ntwf steps
            f.write("  ioutfm=0,\n")  # output formatting
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
    temperature: float = 300.0,
    force_evaluation: ForceEvaluation = ForceEvaluation.Complete,
    bond_constraint: BondLengthConstraint = BondLengthConstraint.NoConstraint,
    write_coordinates_every: int = 1,
    write_velocities_every: int = 0,
    write_forces_every: int = 0,
    periodic_boundary_condition: PeriodicBoundaryCondition = PeriodicBoundaryCondition.NoPeriodicBoundary,
    thermostat: AmberThermostat = AmberThermostat.Langevin,
    ln_gamma: float = 0.5,
):
    """_summary_

    :param mdin_file: File where to write data
    :param nsteps: Number of timesteps to run simulation for
    :param dt: Timestep time in picoseconds, default is 0.001
    :param temperature: Temperature to perform simulation at, default is 300.0
    :param force_evaluation: _description_, defaults to ForceEvaluation.Complete
    :type force_evaluation: ForceEvaluation, optional
    :param bond_constraint: _description_, defaults to BondLengthConstraint.NoConstraint
    :type bond_constraint: BondLengthConstraint, optional
    :param write_coordinates_every: _description_, defaults to 1
    :type write_coordinates_every: int, optional
    :param write_velocities_every: _description_, defaults to -1
    :type write_velocities_every: int, optional
    :param write_forces_every: _description_, defaults to -1
    :type write_forces_every: int, optional
    :param periodic_boundary_condition: _description_, defaults to PeriodicBoundaryCondition.NoPeriodicBoundary
    :type periodic_boundary_condition: PeriodicBoundaryCondition, optional
    :param thermostat: _description_, defaults to AmberThermostat.Langevin
    :type thermostat: AmberThermostat, optional
    :param ln_gamma: _description_, defaults to 0.5
    :type ln_gamma: float, optional
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
    mdcrd: Union[str, Path], # contains geometry
    prmtop: Union[str, Path], # contains atom names
    mdin: Union[str, Path], # contains temperature information
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
