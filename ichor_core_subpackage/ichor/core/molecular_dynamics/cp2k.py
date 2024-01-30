from pathlib import Path
from typing import Optional

from ichor.core.atoms import Atom, Atoms
from ichor.core.files.file import FileContents, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms


class CP2KInput(ReadFile, WriteFile, HasAtoms):
    """CP2K inpuit file reading/writing class.

    :param path: path of CP2K .inp file
    :param atoms: Atoms instance which is the starting geometry, defaults to None
    :param temperature: Temperature of CP2K simulation, defaults to FileContents
    :param nsteps: Timesteps of simulation, defaults to FileContents
    :param datafile_location: The location of a file containing CP2K data.
        This has nothing to do with the `datafile` that ICHOR uses to submit jobs
        , defaults to FileContents
    :param project_name: The name of the system/project, defaults to FileContents
    :param method: The method to use for the DFT simulation, defaults to "BLYP"
    :param basis_set: Basis set to use for simulation, defaults to "6-31G*"
    :param molecular_charge: Charge of system, defaults to 0
    :param n_molecules: Number of molecules, defaults to 1
    :param box_size: Box size of simulation, defaults to 25.0
    """

    _filetype = ".inp"

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
        molecular_charge: int = 0,  # neutral
        spin_multiplicity: int = 1,  # no unpaired electrons
        solver: str = "periodic",
        n_molecules: int = 1,
        box_size: float = 25.0,
    ):

        super(ReadFile, self).__init__(path)

        self.atoms = atoms
        self.temperature = temperature
        self.nsteps = nsteps
        self.datafile_location = datafile_location
        self.project_name = project_name
        self.method: str = method
        self.basis_set: str = basis_set
        self.molecular_charge = molecular_charge
        self.spin_multiplicity = spin_multiplicity
        self.solver: str = solver
        self.n_molecules: int = n_molecules
        self.box_size: float = box_size

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

        write_str = ""

        write_str += "&GLOBAL\n"
        write_str += "  ! the project name is made part of most output files... useful to keep order\n"
        write_str += f"  PROJECT {self.project_name}\n"
        write_str += "  ! various runtypes (energy, geo_opt, etc.) available.\n"
        write_str += "  RUN_TYPE MD\n"
        write_str += "\n"
        write_str += "  IOLEVEL LOW\n"
        write_str += "&END GLOBAL\n"
        write_str += "\n"
        write_str += "&FORCE_EVAL\n"
        write_str += "  ! the electronic structure part of CP2K is named Quickstep\n"
        write_str += "  METHOD Quickstep\n"
        write_str += "  &DFT\n"
        write_str += (
            "    ! basis sets and pseudopotential files can be found in cp2k/data\n"
        )
        write_str += f"    BASIS_SET_FILE_NAME {self.datafile_location / 'BASIS_SET'}\n"
        write_str += (
            f"    POTENTIAL_FILE_NAME {self.datafile_location / 'GTH_POTENTIALS'}\n"
        )
        write_str += "\n"
        write_str += "    ! Charge and multiplicity\n"
        write_str += f"    CHARGE {self.molecular_charge}\n"
        write_str += f"    MULTIPLICITY {self.spin_multiplicity}\n"
        write_str += "\n"
        write_str += "    &MGRID\n"
        write_str += "      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.\n"  # noqa E501
        write_str += "      ! certain calculations (e.g. geometry optimization, vibrational frequencies,\n"
        write_str += "      ! NPT and cell optimizations, need higher cutoffs)\n"
        write_str += "      CUTOFF [Ry] 400\n"  # TODO: Turn this into variable
        write_str += "    &END MGRID\n"
        write_str += "\n"
        write_str += "    &QS\n"
        write_str += "      ! use the GPW method (i.e. pseudopotential based calculations with the Gaussian and Plane Waves scheme).\n"  # noqa E501
        write_str += "      METHOD GPW\n"
        write_str += "      ! default threshold for numerics ~ roughly numerical accuracy of the total energy per electron,\n"  # noqa E501
        write_str += "      ! sets reasonable values for all other thresholds.\n"
        write_str += "      EPS_DEFAULT 1.0E-10\n"
        write_str += (
            "      ! used for MD, the method used to generate the initial guess.\n"
        )
        write_str += "      EXTRAPOLATION ASPC\n"
        write_str += "    &END QS\n"
        write_str += "\n"
        write_str += "    &POISSON\n"
        write_str += "      ! PERIODIC XYZ is the default, gas phase systems should have 'NONE' and a wavelet solver\n"
        if self.solver == "periodic":
            write_str += "      PERIODIC XYZ\n"
        else:
            write_str += "      PERIODIC NONE\n"
        write_str += f"      POISSON_SOLVER {self.solver.upper()}\n"
        write_str += "    &END POISSON\n"
        write_str += "\n"
        write_str += "    ! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.\n"
        write_str += "    &SCF\n"
        write_str += "      SCF_GUESS ATOMIC ! can be used to RESTART an interrupted calculation\n"
        write_str += "      MAX_SCF 30\n"
        write_str += "      EPS_SCF 1.0E-6 ! accuracy of the SCF procedure typically 1.0E-6 - 1.0E-7\n"
        write_str += "      &OT\n"
        write_str += (
            "        ! an accurate preconditioner suitable also for larger systems\n"
        )
        write_str += "        PRECONDITIONER FULL_SINGLE_INVERSE\n"
        write_str += "        ! the most robust choice (DIIS might sometimes be faster, but not as stable).\n"
        write_str += "        MINIMIZER DIIS\n"
        write_str += "      &END OT\n"
        write_str += "      &OUTER_SCF ! repeat the inner SCF cycle 10 times\n"
        write_str += "        MAX_SCF 10\n"
        write_str += "        EPS_SCF 1.0E-6 ! must match the above\n"
        write_str += "      &END\n"
        write_str += "\n"
        write_str += "      &PRINT\n"
        write_str += "        &RESTART OFF\n"  # Turned off for optimisation purposes, may be a good idea to have this as toggleable # noqa E501
        write_str += "        &END\n"
        write_str += "      &END PRINT\n"
        write_str += "    &END SCF\n"
        write_str += "\n"
        write_str += "    ! specify the exchange and correlation treatment\n"
        write_str += "    &XC\n"
        write_str += f"      &XC_FUNCTIONAL {self.method}\n"
        write_str += "      &END XC_FUNCTIONAL\n"
        write_str += (
            "      ! adding Grimme's D3 correction (by default without C9 terms)\n"
        )
        write_str += f"      &VDW_POTENTIAL {'OFF' if self.n_molecules == 1 else ''}\n"
        write_str += "        POTENTIAL_TYPE PAIR_POTENTIAL\n"
        write_str += "        &PAIR_POTENTIAL\n"
        write_str += (
            f"          PARAMETER_FILE_NAME {self.datafile_location / 'dftd3.dat'}\n"
        )
        write_str += "          TYPE DFTD3\n"
        write_str += f"          REFERENCE_FUNCTIONAL {self.method}\n"
        write_str += "          R_CUTOFF [angstrom] 16\n"
        write_str += "        &END PAIR_POTENTIAL\n"
        write_str += "      &END VDW_POTENTIAL\n"
        write_str += "    &END XC\n"
        write_str += "  &END DFT\n"
        write_str += "\n"
        write_str += "  ! description of the system\n"
        write_str += "  &SUBSYS\n"
        write_str += "    &CELL\n"
        write_str += (
            "      ! unit cells that are orthorhombic are more efficient with CP2K\n"
        )
        write_str += (
            f"      ABC [angstrom] {self.box_size} {self.box_size} {self.box_size}\n"
        )
        if self.solver == "wavelet":
            write_str += "      PERIODIC NONE\n"
        write_str += "    &END CELL\n"
        write_str += "\n"
        write_str += "    ! atom coordinates can be in the &COORD section,\n"
        write_str += "    ! or provided as an external file.\n"
        write_str += "    &COORD\n"
        for atom in self.atoms:
            write_str += (
                f"      {atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
            )
        write_str += "    &END COORD\n"
        write_str += "\n"
        write_str += "    ! keep atoms away from box borders,\n"
        write_str += "    ! a requirement for the wavelet Poisson solver\n"
        write_str += "    &TOPOLOGY\n"
        write_str += "      &CENTER_COORDINATES\n"
        write_str += "      &END\n"
        write_str += "    &END TOPOLOGY\n"
        write_str += "\n"
        for atom in self.atoms:
            write_str += f"    &KIND {atom.type.upper()}\n"
            write_str += f"      BASIS_SET {self.basis_set}\n"
            write_str += f"      POTENTIAL GTH-{self.method}-q{atom.valence}\n"
            write_str += "    &END KIND\n"
        write_str += "  &END SUBSYS\n"
        write_str += "&END FORCE_EVAL\n"
        write_str += "\n"
        write_str += "! how to propagate the system, selection via RUN_TYPE in the &GLOBAL section\n"
        write_str += "&MOTION\n"
        write_str += "  &GEO_OPT\n"
        write_str += "    OPTIMIZER LBFGS ! Good choice for 'small' systems (use LBFGS for large systems)\n"
        write_str += "    MAX_ITER  100\n"
        write_str += "    MAX_DR    [bohr] 0.003 ! adjust target as needed\n"
        write_str += "    &BFGS\n"
        write_str += "    &END BFGS\n"
        write_str += "  &END GEO_OPT\n"
        write_str += "  &MD\n"
        write_str += "    ENSEMBLE NVT  ! sampling the canonical ensemble, accurate properties might need NVE\n"
        write_str += f"    TEMPERATURE [K] {self.temperature}\n"
        write_str += (
            "    TIMESTEP [fs] 1.0\n"  # TODO: Turn this into user defined variable
        )
        write_str += f"    STEPS {self.nsteps}\n"
        write_str += "    &THERMOSTAT\n"
        write_str += "      TYPE NOSE\n"
        write_str += "      REGION GLOBAL\n"
        write_str += "      &NOSE\n"
        write_str += "        TIMECON 50.\n"
        write_str += "      &END NOSE\n"
        write_str += "    &END THERMOSTAT\n"
        write_str += "  &END MD\n"
        write_str += "\n"
        write_str += "  &PRINT\n"
        write_str += "    &TRAJECTORY\n"
        write_str += "      &EACH\n"
        write_str += "        MD 1\n"
        write_str += "      &END EACH\n"
        write_str += "    &END TRAJECTORY\n"
        write_str += "    &VELOCITIES OFF\n"
        write_str += "    &END VELOCITIES\n"
        write_str += "    &FORCES OFF\n"
        write_str += "    &END FORCES\n"
        write_str += "    &RESTART OFF\n"
        write_str += "    &END RESTART\n"
        write_str += "    &RESTART_HISTORY OFF\n"
        write_str += "    &END RESTART_HISTORY\n"
        write_str += "  &END PRINT\n"
        write_str += "&END MOTION\n"

        return write_str


def write_cp2k_input(
    cp2k_input_file: Path,
    atoms: Atoms,
    temperature: int,
    nsteps: int,
    datafile_location: Path,
    system_name: str,
    method: str = "BLYP",
    basis_set: str = "6-31G*",
    molecular_charge: int = 0,
    spin_multiplicity: int = 1,
    solver: str = "periodic",
    n_molecules: int = 1,
    box_size: float = 25.0,
):

    project_name = system_name + str(temperature) + "K"

    CP2KInput(
        cp2k_input_file,
        atoms,
        temperature,
        nsteps,
        datafile_location,
        project_name,
        method,
        basis_set,
        molecular_charge,
        spin_multiplicity,
        solver,
        n_molecules,
        box_size,
    ).write()
