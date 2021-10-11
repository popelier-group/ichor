from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np

from ichor.analysis.geometry.geometry_calculator import \
    get_internal_feature_indices
from ichor.atoms import Atom, Atoms
from ichor.common.conversion import try_float
from ichor.common.io import convert_to_path, ln, mkdir, relpath
from ichor.common.str import split_by
from ichor.constants import dlpoly_weights
from ichor.file_structure import FILE_STRUCTURE
from ichor.files.trajectory import Trajectory
from ichor.globals import GLOBALS
from ichor.models import Models
from ichor.units import AtomicDistance


class DlpolyTrajectoryKey(Enum):
    Coordinate = 0
    CoordinateVelocity = 1
    CoordinateVelocityForce = 2


class VelocityNotDefined(Exception):
    pass


class ForceNotDefined(Exception):
    pass


class DlpolyPeriodicBoundary(Enum):
    NoBoundary = 0
    Cubic = 1
    Orthorhombic = 2
    Parallelepiped = 3
    TruncatedOctahedral = 4
    RhombicDodecahedral = 5
    XYParallelogram = 6
    HexagonalPrism = 7


class DlpolyTimestepAtom(Atom):
    def __init__(
        self,
        ty: str = "H",
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        index: Optional[int] = None,
        parent: Optional["Atoms"] = None,
        units: AtomicDistance = AtomicDistance.Angstroms,
    ):
        super(DlpolyTimestepAtom, self).__init__(
            ty, x, y, z, index, parent, units
        )

        atomic_mass = 0.0
        atomic_charge = 0.0

        self._veloctity = None
        self._force = None

    @property
    def velocity(self):
        if self._veloctity is None:
            raise VelocityNotDefined(
                f"Velocity not defined for instance of '{self.__class__.__name__}'"
            )
        return self._veloctity

    @velocity.setter
    def velocity(self, value: np.ndarray):
        self._veloctity = value

    @property
    def force(self):
        if self._force is None:
            raise ForceNotDefined(
                f"Force not defined for instance of '{self.__class__.__name__}'"
            )
        return self._force

    @force.setter
    def force(self, value: np.ndarray):
        self._force = value

    @classmethod
    def from_atom(
        cls, atom: Union[Atom, "DlpolyTimestepAtom"]
    ) -> "DlpolyTimestepAtom":
        inst = DlpolyTimestepAtom(
            atom.type,
            atom.x,
            atom.y,
            atom.z,
            atom.index,
            atom.parent,
            atom.units,
        )
        if isinstance(atom, DlpolyTimestepAtom):
            inst.velocity = atom._velocity
            inst.force = atom._force
        return inst


class DlpolyTimestep(Atoms):
    def __init__(self, atoms: Optional[Sequence[Atom]] = None):
        super().__init__()

        self.unit_cell = np.eye(3)
        self.ntimestep = None
        self.trajectory_key = None
        self.periodic_boundary = None
        self.number_of_atoms = None
        self.timestep_length = None
        self.timestep = None

        if atoms is not None:
            for atom in atoms:
                self.add(DlpolyTimestepAtom.from_atom(atom))


class DlpolyHistory(Trajectory):
    """
    DLPOLY HISTORY File

    Inherits from Trajectory as is a list of Atoms
    Builds on the Trajectory class by adding DLPOLY information
    provided by the HISTORY file
    """

    title: Optional[str]
    trajectory_key: Optional[DlpolyTrajectoryKey]
    periodic_boundary: Optional[DlpolyPeriodicBoundary]
    natoms: Optional[int]
    ntimesteps: Optional[int]

    def __init__(self, path: Optional[Path] = None):
        super(DlpolyHistory, self).__init__(path=path)

        self.title = None

        self.trajectory_key = None
        self.periodic_boundary = None
        self.natoms = None
        self.ntimesteps = None

    def _read_file(self, n: int = -1):
        with open(self.path, "r") as f:
            self.title = next(f)
            record = next(f).split()
            self.trajectory_key = DlpolyTrajectoryKey(int(record[0]))
            self.periodic_boundary = DlpolyTrajectoryKey(int(record[1]))
            self.natoms = int(record[2])
            self.ntimesteps = int(record[3])
            timestep = None
            for line in f:
                if "timestep" in line:
                    if timestep is not None:
                        self.append(timestep)
                    timestep = DlpolyTimestep()

                    record = line.split()
                    # record = 'timestep' ntimestep number_of_atoms keytraj keypbc timestep_length timestep
                    timestep.ntimestep = int(record[1])
                    timestep.number_of_atoms = int(record[2])
                    timestep.trajectory_key = DlpolyTrajectoryKey(
                        int(record[3])
                    )
                    timestep.periodic_boundary = DlpolyPeriodicBoundary(
                        int(record[4])
                    )
                    timestep.timestep_length = float(record[5])
                    timestep.timestep = float(record[6])

                    timestep.unit_cell[0, :] = np.array(
                        [float(ai) for ai in next(f).split()]
                    )  # a vector of unit cell
                    timestep.unit_cell[0, :] = np.array(
                        [float(bi) for bi in next(f).split()]
                    )  # b vector of unit cell
                    timestep.unit_cell[0, :] = np.array(
                        [float(ci) for ci in next(f).split()]
                    )  # c vector of unit cell
                    for _ in range(timestep.number_of_atoms):
                        ta = DlpolyTimestepAtom()

                        record = split_by(next(f), [8, 10, 12, 12])
                        # record = atom_type atom_index atomic_mass charge
                        ta.type = str(record[0])
                        ta.index = int(record[1])
                        ta.atomic_mass = float(record[2])
                        ta.atomic_charge = try_float(
                            record[3], default=0.0
                        )  # can fail if no q00 file is provided

                        ta.coordinates = np.array(
                            [float(ci) for ci in next(f).split()]
                        )

                        if timestep.trajectory_key in [
                            DlpolyTrajectoryKey.CoordinateVelocity,
                            DlpolyTrajectoryKey.CoordinateVelocityForce,
                        ]:
                            ta.velocity = np.array(
                                [float(vi) for vi in next(f).split()]
                            )

                        if (
                            timestep.trajectory_key
                            is DlpolyTrajectoryKey.CoordinateVelocityForce
                        ):
                            ta.force = np.array(
                                [float(fi) for fi in next(f).split()]
                            )

                        timestep.add(ta)
                    self.add(timestep)


def write_control(path: Path, temperature: float = 0.0):
    with open(path / "CONTROL", "w+") as f:
        f.write(f"Title: {GLOBALS.SYSTEM_NAME}\n")
        f.write("\n")
        f.write("ensemble nvt hoover 0.04\n")
        f.write("\n")
        if int(temperature) == 0:
            f.write("temperature 0\n")
            f.write("\n")
            f.write("#perform zero temperature run (really set to 10K)\n")
            f.write("zero\n")
            f.write("\n")
        else:
            f.write(f"temperature {temperature}\n")
            f.write("\n")
        f.write("\n")
        f.write(f"timestep {GLOBALS.DLPOLY_TIMESTEP}\n")
        f.write(f"steps {GLOBALS.DLPOLY_NUMBER_OF_STEPS}\n")
        f.write("scale 100\n")
        f.write("\n")
        f.write("cutoff  8.0\n")
        f.write("rvdw    8.0\n")
        f.write("vdw direct\n")
        f.write("vdw shift\n")
        f.write("fflux cluster L1\n")
        f.write("\n")
        f.write("dump  1000\n")
        f.write("traj 0 1 0\n")
        f.write("print every 1\n")
        f.write("stats every 1\n")
        f.write("fflux print 0 1\n")
        f.write("job time 10000000\n")
        f.write("close time 20000\n")
        f.write("finish\n")


def write_config(path: Path, atoms: Atoms):
    atoms.centre()

    with open(path / "CONFIG", "w+") as f:
        f.write("Frame :         1\n")
        f.write("\t0\t1\n")  # PBC Solution to temporary problem
        f.write("25.0 0.0 0.0\n")
        f.write("0.0 25.0 0.0\n")
        f.write("0.0 0.0 25.0\n")
        for atom in atoms:
            f.write(
                f"{atom.type}  {atom.num}  {GLOBALS.SYSTEM_NAME}_{atom.type}{atom.num}\n"
            )
            f.write(f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n")


def write_field(path: Path, atoms: Atoms):
    bonds, angles, dihedrals = get_internal_feature_indices(atoms)

    with open(path / "FIELD", "w") as f:
        f.write("DL_FIELD v3.00\n")
        f.write("Units kJ/mol\n")
        f.write("Molecular types 1\n")
        f.write(f"{GLOBALS.SYSTEM_NAME}\n")
        f.write("nummols 1\n")
        f.write(f"atoms {len(atoms)}\n")
        for atom in atoms:
            f.write(
                #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
                f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
            )
        f.write(f"BONDS {len(bonds)}\n")
        for i, j in bonds:
            f.write(f"harm {i} {j} 0.0 0.0\n")
        if len(angles) > 0:
            f.write(f"ANGLES {len(angles)}\n")
            for i, j, k in angles:
                f.write(f"harm {i} {j} {k} 0.0 0.0\n")
        if len(dihedrals) > 0:
            f.write(f"DIHEDRALS {len(dihedrals)}\n")
            for i, j, k, l in dihedrals:
                f.write(f"harm {i} {j} {k} {l} 0.0 0.0\n")
        f.write("finish\n")
        f.write("close\n")


def link_models(path: Path, models: Models):
    model_dir = path / "model_krig"
    mkdir(model_dir)
    for model in models:
        ln(model.path.absolute(), model_dir)


def setup_dlpoly_directory(
    path: Path, atoms: Atoms, models: Models, temperature: float = 0.0
):
    mkdir(path)
    write_control(path, temperature=temperature)
    write_config(path, atoms)
    write_field(path, atoms)
    link_models(path, models)


def get_dlpoly_directories(models: List[Models]) -> List[Path]:
    dlpoly_directories = []
    for model in models:
        dlpoly_directories.append(
            FILE_STRUCTURE["dlpoly"]
            / f"{model.system}{str(model.ntrain).zfill(4)}"
        )
    return dlpoly_directories


@convert_to_path
def setup_dlpoly_directories(
    atoms: Atoms, models: List[Models], temperature: float = 0.0
) -> List[Path]:
    dlpoly_directories = get_dlpoly_directories(models)
    for dlpoly_dir, model in zip(dlpoly_directories, models):
        setup_dlpoly_directory(
            dlpoly_dir, atoms, model, temperature=temperature
        )
    return dlpoly_directories
