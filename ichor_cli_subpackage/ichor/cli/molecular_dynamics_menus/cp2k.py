from pathlib import Path
from typing import Optional

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.atoms import Atoms
from ichor.core.common.formatting import (format_number_with_comma,
                                          temperature_formatter)
from ichor.core.common.io import get_files_of_type, mkdir
from ichor.core.common.os import input_with_prefill
from ichor.core.files import GJF, XYZ, Trajectory
from ichor.core.menu import Menu, MenuVar, set_number
from ichor.hpc import FILE_STRUCTURE, GLOBALS, MACHINE, Machine
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, CP2KCommand,
                                         SubmissionScript)

INPUT_FILETYPES = [XYZ.filetype, GJF.filetype]

datafile_location = {
    Machine.ffluxlab: Path("/home/modules/apps/cp2k/6.1.0/data"),
    Machine.csf3: Path("/opt/apps/apps/intel-17.0/cp2k/6.1.0/data"),
    Machine.local: Path("$CP2K_HOME/data"),
}


# todo: move to hpc/core


def write_cp2k_input(
    cp2k_input_file: Path,
    atoms: Atoms,
    temperature: float,
    nsteps: int,
    solver: str = "periodic",
    n_molecules: int = 1,
    box_size: float = 25.0,
):
    atoms.centre()
    with open(cp2k_input_file, "w") as f:
        f.write("&GLOBAL\n")
        f.write(
            "  ! the project name is made part of most output files... useful to keep order\n"
        )
        f.write(f"  PROJECT {GLOBALS.SYSTEM_NAME}\n")
        f.write("  ! various runtypes (energy, geo_opt, etc.) available.\n")
        f.write("  RUN_TYPE MD\n")
        f.write("\n")
        f.write("  IOLEVEL LOW\n")
        f.write("&END GLOBAL\n")
        f.write("\n")
        f.write("&FORCE_EVAL\n")
        f.write(
            "  ! the electronic structure part of CP2K is named Quickstep\n"
        )
        f.write("  METHOD Quickstep\n")
        f.write("  &DFT\n")
        f.write(
            "    ! basis sets and pseudopotential files can be found in cp2k/data\n"
        )
        f.write(
            f"    BASIS_SET_FILE_NAME {datafile_location[MACHINE]}/BASIS_SET\n"
        )
        f.write(
            f"    POTENTIAL_FILE_NAME {datafile_location[MACHINE]}/GTH_POTENTIALS\n"
        )
        f.write("\n")
        f.write("    ! Charge and multiplicity\n")
        f.write("    CHARGE 0\n")  # TODO: Handle Charged Molecules
        f.write("    MULTIPLICITY 1\n")
        f.write("\n")
        f.write("    &MGRID\n")
        f.write(
            "      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.\n"
        )
        f.write(
            "      ! certain calculations (e.g. geometry optimization, vibrational frequencies,\n"
        )
        f.write("      ! NPT and cell optimizations, need higher cutoffs)\n")
        f.write("      CUTOFF [Ry] 400\n")  # TODO: Turn this into variable
        f.write("    &END MGRID\n")
        f.write("\n")
        f.write("    &QS\n")
        f.write(
            "      ! use the GPW method (i.e. pseudopotential based calculations with the Gaussian and Plane Waves scheme).\n"
        )
        f.write("      METHOD GPW\n")
        f.write(
            "      ! default threshold for numerics ~ roughly numerical accuracy of the total energy per electron,\n"
        )
        f.write("      ! sets reasonable values for all other thresholds.\n")
        f.write("      EPS_DEFAULT 1.0E-10\n")
        f.write(
            "      ! used for MD, the method used to generate the initial guess.\n"
        )
        f.write("      EXTRAPOLATION ASPC\n")
        f.write("    &END QS\n")
        f.write("\n")
        f.write("    &POISSON\n")
        f.write(
            "      ! PERIODIC XYZ is the default, gas phase systems should have 'NONE' and a wavelet solver\n"
        )
        if solver == "periodic":
            f.write("      PERIODIC XYZ\n")
        else:
            f.write("      PERIODIC NONE\n")
        f.write(f"      POISSON_SOLVER {solver.upper()}\n")
        f.write("    &END POISSON\n")
        f.write("\n")
        f.write(
            "    ! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.\n"
        )
        f.write("    &SCF\n")
        f.write(
            "      SCF_GUESS ATOMIC ! can be used to RESTART an interrupted calculation\n"
        )
        f.write("      MAX_SCF 30\n")
        f.write(
            "      EPS_SCF 1.0E-6 ! accuracy of the SCF procedure typically 1.0E-6 - 1.0E-7\n"
        )
        f.write("      &OT\n")
        f.write(
            "        ! an accurate preconditioner suitable also for larger systems\n"
        )
        f.write("        PRECONDITIONER FULL_SINGLE_INVERSE\n")
        f.write(
            "        ! the most robust choice (DIIS might sometimes be faster, but not as stable).\n"
        )
        f.write("        MINIMIZER DIIS\n")
        f.write("      &END OT\n")
        f.write("      &OUTER_SCF ! repeat the inner SCF cycle 10 times\n")
        f.write("        MAX_SCF 10\n")
        f.write("        EPS_SCF 1.0E-6 ! must match the above\n")
        f.write("      &END\n")
        f.write("\n")
        f.write("      &PRINT\n")
        f.write(
            "        &RESTART OFF\n"
        )  # Turned off for optimisation purposes, may be a good idea to have this as toggleable
        f.write("        &END\n")
        f.write("      &END PRINT\n")
        f.write("    &END SCF\n")
        f.write("\n")
        f.write("    ! specify the exchange and correlation treatment\n")
        f.write("    &XC\n")
        f.write(f"      &XC_FUNCTIONAL {GLOBALS.CP2K_METHOD}\n")
        f.write("      &END XC_FUNCTIONAL\n")
        f.write(
            "      ! adding Grimme's D3 correction (by default without C9 terms)\n"
        )
        f.write(f"      &VDW_POTENTIAL {'OFF' if n_molecules == 1 else ''}\n")
        f.write("        POTENTIAL_TYPE PAIR_POTENTIAL\n")
        f.write("        &PAIR_POTENTIAL\n")
        f.write(
            f"          PARAMETER_FILE_NAME {datafile_location[MACHINE]}/dftd3.dat\n"
        )
        f.write("          TYPE DFTD3\n")
        f.write(f"          REFERENCE_FUNCTIONAL {GLOBALS.CP2K_METHOD}\n")
        f.write("          R_CUTOFF [angstrom] 16\n")
        f.write("        &END PAIR_POTENTIAL\n")
        f.write("      &END VDW_POTENTIAL\n")
        f.write("    &END XC\n")
        f.write("  &END DFT\n")
        f.write("\n")
        f.write("  ! description of the system\n")
        f.write("  &SUBSYS\n")
        f.write("    &CELL\n")
        f.write(
            "      ! unit cells that are orthorhombic are more efficient with CP2K\n"
        )
        f.write(f"      ABC [angstrom] {box_size} {box_size} {box_size}\n")
        if solver == "wavelet":
            f.write("      PERIODIC NONE\n")
        f.write("    &END CELL\n")
        f.write("\n")
        f.write("    ! atom coordinates can be in the &COORD section,\n")
        f.write("    ! or provided as an external file.\n")
        f.write("    &COORD\n")
        for atom in atoms:
            f.write(
                f"      {atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
            )
        f.write("    &END COORD\n")
        f.write("\n")
        f.write("    ! keep atoms away from box borders,\n")
        f.write("    ! a requirement for the wavelet Poisson solver\n")
        f.write("    &TOPOLOGY\n")
        f.write("      &CENTER_COORDINATES\n")
        f.write("      &END\n")
        f.write("    &END TOPOLOGY\n")
        f.write("\n")
        for atom in atoms:
            f.write(f"    &KIND {atom.type.upper()}\n")
            f.write(f"      BASIS_SET {GLOBALS.CP2K_BASIS_SET}\n")
            f.write(
                f"      POTENTIAL GTH-{GLOBALS.CP2K_METHOD}-q{atom.valence}\n"
            )
            f.write("    &END KIND\n")
        f.write("  &END SUBSYS\n")
        f.write("&END FORCE_EVAL\n")
        f.write("\n")
        f.write(
            "! how to propagate the system, selection via RUN_TYPE in the &GLOBAL section\n"
        )
        f.write("&MOTION\n")
        f.write("  &GEO_OPT\n")
        f.write(
            "    OPTIMIZER LBFGS ! Good choice for 'small' systems (use LBFGS for large systems)\n"
        )
        f.write("    MAX_ITER  100\n")
        f.write("    MAX_DR    [bohr] 0.003 ! adjust target as needed\n")
        f.write("    &BFGS\n")
        f.write("    &END BFGS\n")
        f.write("  &END GEO_OPT\n")
        f.write("  &MD\n")
        f.write(
            "    ENSEMBLE NVT  ! sampling the canonical ensemble, accurate properties might need NVE\n"
        )
        f.write(f"    TEMPERATURE [K] {temperature}\n")
        f.write(
            "    TIMESTEP [fs] 1.0\n"
        )  # TODO: Turn this into user defined variable
        f.write(f"    STEPS {nsteps}\n")
        f.write("    &THERMOSTAT\n")
        f.write("      TYPE NOSE\n")
        f.write("      REGION GLOBAL\n")
        f.write("      &NOSE\n")
        f.write("        TIMECON 50.\n")
        f.write("      &END NOSE\n")
        f.write("    &END THERMOSTAT\n")
        f.write("  &END MD\n")
        f.write("\n")
        f.write("  &PRINT\n")
        f.write("    &TRAJECTORY\n")
        f.write("      &EACH\n")
        f.write("        MD 1\n")
        f.write("      &END EACH\n")
        f.write("    &END TRAJECTORY\n")
        f.write("    &VELOCITIES OFF\n")
        f.write("    &END VELOCITIES\n")
        f.write("    &FORCES OFF\n")
        f.write("    &END FORCES\n")
        f.write("    &RESTART OFF\n")
        f.write("    &END RESTART\n")
        f.write("    &RESTART_HISTORY OFF\n")
        f.write("    &END RESTART_HISTORY\n")
        f.write("  &END PRINT\n")
        f.write("&END MOTION\n")


def submit_cp2k(input_file: Path, temperature: float, nsteps: int) -> JobID:
    if input_file.suffix == XYZ.filetype:
        atoms = XYZ(input_file).atoms
    elif input_file.suffix == GJF.filetype:
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    mkdir(FILE_STRUCTURE["cp2k"])
    cp2k_input = FILE_STRUCTURE["cp2k"] / f"{GLOBALS.SYSTEM_NAME}.inp"
    write_cp2k_input(cp2k_input, atoms, temperature, nsteps)

    with SubmissionScript(SCRIPT_NAMES["cp2k"]) as submission_script:
        submission_script.add_command(CP2KCommand(cp2k_input, temperature))
    return submission_script.submit()


def cp2k_to_xyz(
    cp2k_input: Path,
    xyz: Optional[Path] = None,
    temperature: Optional[float] = None,
) -> Path:
    xyzs = get_files_of_type(Trajectory.filetype, cp2k_input.parent)
    if len(xyzs) == 0:
        raise FileNotFoundError(
            f"No trajectory files found in {cp2k_input.parent}"
        )
    traj = Trajectory(xyzs[0])
    if xyz is None:
        path = "{GLOBALS.SYSTEM_NAME}-cp2k"
        if temperature is not None:
            path += f"{int(temperature)}"
        path += f"{Trajectory.filetype}"
        xyz = Path(path)
    traj.write(xyz)
    return xyz


def set_input(input_file: MenuVar[Path]):
    input_file.var = get_input_menu(input_file.var, INPUT_FILETYPES)


def cp2k_menu():
    input_file = MenuVar("Input File", get_first_file(Path(), INPUT_FILETYPES))
    temperature = MenuVar(
        "Temperature",
        GLOBALS.CP2K_TEMPERATURE,
        custom_formatter=temperature_formatter,
    )
    nsteps = MenuVar(
        "Number of Timesteps",
        GLOBALS.CP2K_STEPS,
        custom_formatter=format_number_with_comma,
    )

    with Menu("CP2K Menu") as menu:
        menu.add_option(
            "1",
            "Run CP2K",
            submit_cp2k,
            args=[input_file, temperature, nsteps],
        )
        menu.add_space()
        menu.add_option("i", "Set input file", set_input, args=[input_file])
        menu.add_option("t", "Set Temperature", set_number, args=[temperature])
        menu.add_option(
            "n", "Set number of timesteps", set_number, args=[nsteps]
        )
        menu.add_space()
        menu.add_var(input_file)
        menu.add_var(temperature)
        menu.add_var(nsteps)
