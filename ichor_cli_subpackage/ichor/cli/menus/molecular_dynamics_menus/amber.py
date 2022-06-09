from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.formatting import (
    format_number_with_comma,
    temperature_formatter,
)
from ichor.core.common.io import mkdir
from ichor.core.common.os import input_with_prefill
from ichor.core.files import GJF, XYZ, Mol2, Trajectory
from ichor.core.menu import Menu, MenuVar, set_number
from ichor.hpc import FILE_STRUCTURE, GLOBALS
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    AmberCommand,
    SubmissionScript,
)

# todo: put this in core


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


THERMOSTAT = AmberThermostat.Langevin
BOND_CONSTRAINT = BondLengthConstraint.NoConstraint
FORCE_EVALUATION = ForceEvaluation.Complete
PBC = PeriodicBoundaryCondition.NoPeriodicBoundary

input_filetypes = [XYZ.filetype, GJF.filetype]

_write_coord_every = 1
_write_vel_every = 0
_write_forces_every = 0


def write_mdin(mdin_file: Path):
    with open(mdin_file, "w") as f:
        f.write("Production\n")
        f.write(" &cntrl\n")
        f.write("  imin=0,\n")  # not running minimisation
        f.write("  ntx=1,\n")  # read input coordinates only
        f.write("  irest=0,\n")  # not restarting simulation
        f.write(f"  nstlim={GLOBALS.AMBER_STEPS},\n")  # number of time steps
        f.write(
            f"  dt={GLOBALS.AMBER_TIMESTEP},\n"
        )  # time step in picoseconds
        f.write(f"  ntf={FORCE_EVALUATION.value},\n")  # force constraint
        f.write(f"  ntc={BOND_CONSTRAINT.value},\n")  # bond contraint
        f.write(f"  temp0={GLOBALS.AMBER_TEMPERATURE},\n")  # temperature
        f.write("  ntpr=1,\n")  # energy info printed to mdout every ntpr steps
        f.write(
            f"  ntwx={_write_coord_every},\n"
        )  # coordinate info printed to mdout every ntwx steps
        f.write(
            f"  ntwv={_write_vel_every},\n"
        )  # velocity info printed to mdout every ntwv steps
        f.write(
            f"  ntwf={_write_forces_every},\n"
        )  # force info printed to mdout every ntwf steps
        f.write("  ioutfm=0,\n")  # output formatting
        f.write("  cut=999.0,\n")  # nonbonded cutoff
        f.write(f"  ntb={PBC.value},\n")  # periodic boundary conditions
        f.write("  ntp=0,\n")  # pressure control
        f.write(f"  ntt={THERMOSTAT.value},\n")  # thermostat
        f.write(
            f"  gamma_ln={GLOBALS.AMBER_LN_GAMMA},\n"
        )  # ln(gamma) for the langevin thermostat
        f.write("  tempi=0.0,\n")  # temperature to initialise velocities
        f.write("  ig=-1\n")  # random seed (-1 randomises seed)
        f.write(" /\n")


def submit_amber(input_file: Path, temperature: float) -> JobID:
    if input_file.suffix == XYZ.filetype:
        atoms = XYZ(input_file).atoms
    elif input_file.suffix == GJF.filetype:
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    nres = 1  # number of residues is fixed at 1 as we aren't hydrating
    GLOBALS.AMBER_NCORES = min(
        GLOBALS.AMBER_NCORES, nres
    )  # ncores must be less than or equal to the number of residues

    mkdir(FILE_STRUCTURE["amber"])
    mol2 = Mol2(
        FILE_STRUCTURE["amber"] / (GLOBALS.SYSTEM_NAME + Mol2.filetype)
    )
    mol2.atoms = atoms
    mol2.write()

    mdin = FILE_STRUCTURE["amber"] / "md.in"
    write_mdin(mdin)

    with SubmissionScript(SCRIPT_NAMES["amber"]) as submission_script:
        submission_script.add_command(
            AmberCommand(mol2.path, mdin, temperature)
        )
    return submission_script.submit()


def mdcrd_to_xyz(
    mdcrd: Path, prmtop: Path, xyz: Optional[Path] = None, every: int = 1
):
    atom_names = []
    with open(prmtop, "r") as f:
        for line in f:
            if "ATOM_NAME" in line:
                _ = next(f)
                line = next(f)
                while "CHARGE" not in line:
                    atom_names += [a[0] for a in line.split()]
                    line = next(f)

    if xyz is None:
        xyz = Path(
            f"{GLOBALS.SYSTEM_NAME}-amber-{int(GLOBALS.AMBER_TEMPERATURE)}.xyz"
        )

    natoms = len(atom_names)
    with open(mdcrd, "r") as f:
        _ = next(f)
        traj = np.array([])
        i = 0
        with open(xyz, "w") as o:
            for line in f:
                traj = np.hstack(
                    (traj, np.array(line.split(), dtype=np.float))
                )
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


def set_input(input_file: MenuVar[Path]):
    input_file.var = get_input_menu(input_file.var, input_filetypes)


def timestep_formatter(write_every: int) -> str:
    return f"'{write_every}' timestep(s)"


def amber_menu():
    input_file = MenuVar("Input File", get_first_file(Path(), input_filetypes))
    temperature = MenuVar(
        "Temperature",
        GLOBALS.AMBER_TEMPERATURE,
        custom_formatter=temperature_formatter,
    )
    nsteps = MenuVar(
        "Number of Timesteps",
        GLOBALS.AMBER_STEPS,
        custom_formatter=format_number_with_comma,
    )
    write_coord_every = MenuVar(
        "Write Output Every",
        GLOBALS.AMBER_STEPS,
        custom_formatter=timestep_formatter,
    )
    with Menu("Amber Menu") as menu:
        menu.add_option(
            "1", "Run Amber", submit_amber, args=[input_file, temperature]
        )
        menu.add_space()
        menu.add_option("i", "Set input file", set_input, args=[input_file])
        menu.add_option("t", "Set Temperature", set_number, args=[temperature])
        menu.add_option(
            "n", "Set number of timesteps", set_number, args=[nsteps]
        )
        menu.add_option(
            "e",
            "Set print every n timesteps",
            set_number,
            args=[write_coord_every],
        )
        menu.add_space()
        menu.add_var(input_file)
        menu.add_var(temperature)
        menu.add_var(nsteps)
        menu.add_var(write_coord_every)
