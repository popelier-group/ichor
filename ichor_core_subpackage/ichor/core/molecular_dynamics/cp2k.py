from pathlib import Path
from typing import Optional

from ichor.core.analysis.get_input import get_files_of_type
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.files import (
    File,
    FileContents,
    HasAtoms,
    ReadFile,
    Trajectory,
    WriteFile,
)


class CP2KInput(ReadFile, WriteFile, File, HasAtoms):
    def __init__(
        self,
        path: Path,
        atoms: Optional[Atoms] = None,
        temperature: float = FileContents,
        nsteps: int = FileContents,
        datafile_location: Path = FileContents,
        project_name: str = FileContents,
        method: str = "BLYP",
        basis_set: str = "6-31G*",
        solver: str = "periodic",
        n_molecules: int = 1,
        box_size: float = 25.0,
    ):
        File.__init__(self, path)
        HasAtoms.__init__(self, atoms)
        self.temperature = temperature
        self.nsteps = nsteps
        self.datafile_location = datafile_location
        self.project_name = project_name
        self.method: str = method
        self.basis_set: str = basis_set
        self.solver: str = solver
        self.n_molecules: int = n_molecules
        self.box_size: float = box_size

    @classproperty
    def filetype(self) -> str:
        return ".inp"

    def _read_file(self):
        self.atoms = Atoms()
        self.n_molecules = 1
        with open(self.path, "r") as f:
            for line in f:
                if "PROJECT" in line:
                    self.project_name = line.split()[1]
                elif "BASIS_SET_FILE_NAME" in line:
                    self.datafile_location = Path(line.split()[-1]).parent
                elif "POISSON_SOLVER" in line:
                    self.solver = line.split()[1]
                elif "BASIS_SET" in line:
                    self.basis_set = line.split()[1]
                elif "REFERENCE_FUNCTIONAL" in line:
                    self.method = line.split()[1]
                elif "ABC" in line:
                    self.box_size = float(line.split()[2])
                elif "&COORD" in line:
                    line = next(f)
                    while "&END COORD" not in line:
                        record = line.split()
                        ty = record[0]
                        x = float(record[1])
                        y = float(record[2])
                        z = float(record[3])
                        self.atoms.add(Atom(ty, x, y, z))
                        line = next(f)
                elif "TEMPERATURE" in line:
                    self.temperature = float(line.split()[-1])
                elif "STEPS" in line:
                    self.nsteps = int(line.split()[-1])

    def _write_file(self, path: Path):
        self.atoms.centre()
        with open(path, "w") as f:
            f.write("&GLOBAL\n")
            f.write(
                "  ! the project name is made part of most output files... useful to keep order\n"
            )
            f.write(f"  PROJECT {self.project_name}\n")
            f.write(
                "  ! various runtypes (energy, geo_opt, etc.) available.\n"
            )
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
                f"    BASIS_SET_FILE_NAME {self.datafile_location / 'BASIS_SET'}\n"
            )
            f.write(
                f"    POTENTIAL_FILE_NAME {self.datafile_location / 'GTH_POTENTIALS'}\n"
            )
            f.write("\n")
            f.write("    ! Charge and multiplicity\n")
            f.write(f"    CHARGE {self.atoms.nuclear_charge}\n")
            f.write("    MULTIPLICITY 1\n")
            f.write("\n")
            f.write("    &MGRID\n")
            f.write(
                "      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.\n"
            )
            f.write(
                "      ! certain calculations (e.g. geometry optimization, vibrational frequencies,\n"
            )
            f.write(
                "      ! NPT and cell optimizations, need higher cutoffs)\n"
            )
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
            f.write(
                "      ! sets reasonable values for all other thresholds.\n"
            )
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
            if self.solver == "periodic":
                f.write("      PERIODIC XYZ\n")
            else:
                f.write("      PERIODIC NONE\n")
            f.write(f"      POISSON_SOLVER {self.solver.upper()}\n")
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
            f.write(f"      &XC_FUNCTIONAL {self.method}\n")
            f.write("      &END XC_FUNCTIONAL\n")
            f.write(
                "      ! adding Grimme's D3 correction (by default without C9 terms)\n"
            )
            f.write(
                f"      &VDW_POTENTIAL {'OFF' if self.n_molecules == 1 else ''}\n"
            )
            f.write("        POTENTIAL_TYPE PAIR_POTENTIAL\n")
            f.write("        &PAIR_POTENTIAL\n")
            f.write(
                f"          PARAMETER_FILE_NAME {self.datafile_location / 'dftd3.dat'}\n"
            )
            f.write("          TYPE DFTD3\n")
            f.write(f"          REFERENCE_FUNCTIONAL {self.method}\n")
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
            f.write(
                f"      ABC [angstrom] {self.box_size} {self.box_size} {self.box_size}\n"
            )
            if self.solver == "wavelet":
                f.write("      PERIODIC NONE\n")
            f.write("    &END CELL\n")
            f.write("\n")
            f.write("    ! atom coordinates can be in the &COORD section,\n")
            f.write("    ! or provided as an external file.\n")
            f.write("    &COORD\n")
            for atom in self.atoms:
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
            for atom in self.atoms:
                f.write(f"    &KIND {atom.type.upper()}\n")
                f.write(f"      BASIS_SET {self.basis_set}\n")
                f.write(f"      POTENTIAL GTH-{self.method}-q{atom.valence}\n")
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
            f.write(f"    TEMPERATURE [K] {self.temperature}\n")
            f.write(
                "    TIMESTEP [fs] 1.0\n"
            )  # TODO: Turn this into user defined variable
            f.write(f"    STEPS {self.nsteps}\n")
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


def write_cp2k_input(
    cp2k_input_file: Path,
    atoms: Atoms,
    temperature: float,
    nsteps: int,
    datafile_location: Path,
    project_name: str = "CP2K",
    method: str = "BLYP",
    basis_set: str = "6-31G*",
    solver: str = "periodic",
    n_molecules: int = 1,
    box_size: float = 25.0,
):
    CP2KInput(
        cp2k_input_file,
        atoms,
        temperature,
        nsteps,
        datafile_location,
        project_name,
        method,
        basis_set,
        solver,
        n_molecules,
        box_size,
    ).write()


def cp2k_to_xyz(
    cp2k_input: Path,
    xyz: Optional[Path] = None,
    temperature: Optional[float] = None,
) -> Path:
    if xyz is None:
        xyzs = get_files_of_type(Trajectory.filetype, cp2k_input.parent)
        if len(xyzs) == 0:
            raise FileNotFoundError(
                f"No trajectory files found in {cp2k_input.parent}"
            )
        xyz = xyz[0]
    traj = Trajectory(xyz)
    if xyz is None:
        cp2k_input = CP2KInput(cp2k_input)
        temperature = (
            cp2k_input.temperature if temperature is None else temperature
        )
        path = f"{cp2k_input.project_name}-cp2k-{temperature}{Trajectory.filetype}"
        xyz = Path(path)
    traj.write(xyz)
    return xyz
