from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.io import convert_to_path
from ichor.core.common.str import split_by
from ichor.core.common.units import AtomicDistance
from ichor.core.files.file import FileContents
from ichor.core.files.xyz import Trajectory


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
        ty: str,
        x: float,
        y: float,
        z: float,
        index: Optional[int] = None,
        parent: Optional["Atoms"] = None,
        units: AtomicDistance = AtomicDistance.Angstroms,
        velocity=None,
        force=None,
    ):
        super(DlpolyTimestepAtom, self).__init__(ty, x, y, z, index, parent, units)

        self._veloctity = velocity
        self._force = force

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


class DlpolyTimestep(Atoms):
    def __init__(self):

        super().__init__()

        self.unit_cell = np.eye(3)
        self.ntimestep = None
        self.trajectory_key = None
        self.periodic_boundary = None
        self.number_of_atoms = None
        self.timestep_length = None
        self.timestep = None


class DlpolyHistory(Trajectory):
    """
    DLPOLY HISTORY File

    Inherits from Trajectory as is a list of Atoms
    Builds on the Trajectory class by adding DLPOLY information
    provided by the HISTORY file

    .. warning::
        Indexing the history as a python list, i.e. history[1000]
        is not guaranteed to give the 1000th timestep (0-indexed).
        This is because sometimes there is binary written to the HISTORY
        file which messes up some geometries. These geometries are excluded
        from the read in data, so indexing as a list will might return a
        different timestep.

        To make sure that the exact timestep is returned (useful when you
        also want to get data from FFLUX or IQA_ENERGIES/IQA_FORCES file,
        then ensure that you check the ``ntimestep`` attribute of a timestep).
        This will be correct, even if some geoemtries are missing.

        To get a list of missing timesteps, use the self.removed_timesteps attribute
        of the DlPolyHistory class.

    """

    _filetype = ""

    def __init__(self, path: Optional[Path] = Path("HISTORY")):

        super().__init__(path)

        self.title = FileContents
        self.trajectory_key = FileContents
        self.periodic_boundary = FileContents
        self.number_of_atoms = FileContents
        self.ntimesteps = FileContents
        self.existing_timesteps = FileContents
        self.removed_timesteps = FileContents

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.stem == "HISTORY"

    def _read_file(self):

        # we will read the first lines to get number of atoms
        # then read in a chunk of lines, if binary is encountered then discard all geometries
        # this will likely discard extra geometries, but will ensure that
        # all geometries are read in correctly at least

        try:

            with open(self.path, "r") as f:

                line = next(f)
                self.title = line
                line = next(f)
                record = line.split()
                self.trajectory_key = DlpolyTrajectoryKey(int(record[0]))
                self.periodic_boundary = DlpolyTrajectoryKey(int(record[1]))
                self.number_of_atoms = int(record[2])
                self.ntimesteps = int(record[3])

                # read number of lines depending of whether
                # coordinates, velocities, and/or forces are written in the file
                if self.trajectory_key is DlpolyTrajectoryKey.Coordinate:
                    nlines_to_read = self.number_of_atoms * 2 + 3
                elif self.trajectory_key is DlpolyTrajectoryKey.CoordinateVelocity:
                    nlines_to_read = self.number_of_atoms * 3 + 3
                elif self.trajectory_key is DlpolyTrajectoryKey.CoordinateVelocityForce:
                    nlines_to_read = self.number_of_atoms * 4 + 3

                while True:

                    # default is that the timestep does not contain binary
                    timestep_contains_binary = False

                    line = next(f)
                    # if timestep is in beginning of line, this should be beginning of geometry
                    # and there should not be binary in that line
                    if "timestep" == line.split()[0]:

                        this_timestep_lines = []
                        this_timestep_lines.append(line)
                        for _ in range(nlines_to_read):
                            line = next(f)
                            this_timestep_lines.append(line)

                        # check if any line has binary
                        # if it does, then do not add this timestep
                        # doing so might also remove next timesteps
                        # because of lines missing that are read from the next geometry
                        for i in this_timestep_lines:
                            if "\x00" in i:
                                timestep_contains_binary = True
                                break

                        # if there is no binary in timestep, then it should have clean
                        # data, so we can read it as normal
                        # iterate over the list containing all tines for this timestep
                        if not timestep_contains_binary:

                            this_timestep_lines = iter(this_timestep_lines)

                            timestep = DlpolyTimestep()

                            # loop over lines in the timestep that has been read in
                            line = next(this_timestep_lines)
                            # record = 'timestep' ntimestep number_of_atoms keytraj keypbc timestep_length timestep
                            record = line.split()
                            # since this timestep not contain binary
                            # the timestep that is in the file should be correct
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
                                [float(ai) for ai in next(this_timestep_lines).split()]
                            )  # a vector of unit cell
                            timestep.unit_cell[1, :] = np.array(
                                [float(bi) for bi in next(this_timestep_lines).split()]
                            )  # b vector of unit cell
                            timestep.unit_cell[2, :] = np.array(
                                [float(ci) for ci in next(this_timestep_lines).split()]
                            )  # c vector of unit cell

                            for _ in range(timestep.number_of_atoms):

                                line = next(this_timestep_lines)
                                # record = atom_type atom_index atomic_mass charge
                                record = split_by(line, [8, 10, 12, 12])

                                timestep_atom_type = str(record[0])

                                line = next(this_timestep_lines)
                                timestep_atom_coordinates = np.array(
                                    [float(ci) for ci in line.split()]
                                )

                                timestep_atom = DlpolyTimestepAtom(
                                    timestep_atom_type,
                                    timestep_atom_coordinates[0],
                                    timestep_atom_coordinates[1],
                                    timestep_atom_coordinates[2],
                                )

                                if timestep.trajectory_key in [
                                    DlpolyTrajectoryKey.CoordinateVelocity,
                                    DlpolyTrajectoryKey.CoordinateVelocityForce,
                                ]:
                                    timestep_atom.velocity = np.array(
                                        [
                                            float(vi)
                                            for vi in next(this_timestep_lines).split()
                                        ]
                                    )

                                if (
                                    timestep.trajectory_key
                                    is DlpolyTrajectoryKey.CoordinateVelocityForce
                                ):
                                    timestep_atom.force = np.array(
                                        [
                                            float(fi)
                                            for fi in next(this_timestep_lines).split()
                                        ]
                                    )

                                timestep.add(timestep_atom)

                            # this timestep should be safe to add
                            # and no binary data should be present
                            self.add(timestep)

        except StopIteration:
            # these are the timesteps that are read in
            # get the ntimestep attribute
            # which should always be correct even if data is missing
            existing_timesteps = [i.ntimestep for i in self]

            # these are the missing timesteps because of binary in HISTORY file
            removed_timesteps = []
            # loop over all timesteps that are in the HISTORY file
            # note that the initial geometry is also counted a timestep
            # so setting the CONTROL timesteps to 500 for example will give 501 geometries in HISTORY file
            for i in range(self.ntimesteps):
                if i not in existing_timesteps:
                    removed_timesteps.append(i)

            self.existing_timesteps = existing_timesteps
            self.removed_timesteps = removed_timesteps

    # TODO: potentially return this implementation once the issues with
    # binary code in the HISTORY file is resolved.

    # def _read_file(self):

    #     with open(self.path, "r") as f:

    #         self.title = next(f)
    #         record = next(f).split()
    #         self.trajectory_key = DlpolyTrajectoryKey(int(record[0]))
    #         self.periodic_boundary = DlpolyTrajectoryKey(int(record[1]))
    #         self.number_of_atoms = int(record[2])
    #         self.ntimesteps = int(record[3])

    #         removed_timesteps = []
    #         timestep_contains_binary = False

    #         try:
    #             while True:

    #                 # sometimes binary data is written in HISTORY file
    #                 # the binary is written to the same line as the next line that contains timestep info
    #                 if not timestep_contains_binary:
    #                     line = next(f)

    #                 # reset the variables used to check if the timestep contains binary data
    #                 add_this_timestep = True
    #                 timestep_contains_binary = False

    #                 if "timestep" in line:

    #                     # used for dealing with binary data in HISTORY file sometimes
    #                     # ideally this issue should be fixed in FFLUX
    #                     timestep = DlpolyTimestep()

    #                     # record = 'timestep' ntimestep number_of_atoms keytraj keypbc timestep_length timestep
    #                     record = line.split()
    #                     if "\x00" in record[0]:
    #                         del record[0]
    #                     timestep.ntimestep = int(record[1])
    #                     timestep.number_of_atoms = int(record[2])
    #                     timestep.trajectory_key = DlpolyTrajectoryKey(int(record[3]))
    #                     timestep.periodic_boundary = DlpolyPeriodicBoundary(
    #                         int(record[4])
    #                     )
    #                     timestep.timestep_length = float(record[5])
    #                     timestep.timestep = float(record[6])

    #                     timestep.unit_cell[0, :] = np.array(
    #                         [float(ai) for ai in next(f).split()]
    #                     )  # a vector of unit cell
    #                     timestep.unit_cell[1, :] = np.array(
    #                         [float(bi) for bi in next(f).split()]
    #                     )  # b vector of unit cell
    #                     timestep.unit_cell[2, :] = np.array(
    #                         [float(ci) for ci in next(f).split()]
    #                     )  # c vector of unit cell

    #                     for _ in range(timestep.number_of_atoms):

    #                         # for some reason binary is being written to the HISTORY file sometimes
    #                         # this then causes issues with parsing
    #                         # if the line has timestep in it, it means that the geometry is missing
    #                         line = next(f)
    #                         if "timestep" in line:
    #                             # do not add timestep to the resulting history
    #                             # ie history will have 1 less timestep
    #                             add_this_timestep = False
    #                             # this variable is used in the beginning of the while loop
    #                             # setting to True means that the next(f) would not be called
    #                             timestep_contains_binary = True
    #                             # add the messed up timestep to a list
    #                             removed_timesteps.append(timestep.ntimestep)
    #                             break

    #                         # record = atom_type atom_index atomic_mass charge
    #                         record = split_by(line, [8, 10, 12, 12])

    #                         timestep_atom_type = str(record[0])

    #                         timestep_atom_coordinates = np.array(
    #                             [float(ci) for ci in next(f).split()]
    #                         )

    #                         timestep_atom = DlpolyTimestepAtom(
    #                             timestep_atom_type,
    #                             timestep_atom_coordinates[0],
    #                             timestep_atom_coordinates[1],
    #                             timestep_atom_coordinates[2],
    #                         )

    #                         if timestep.trajectory_key in [
    #                             DlpolyTrajectoryKey.CoordinateVelocity,
    #                             DlpolyTrajectoryKey.CoordinateVelocityForce,
    #                         ]:
    #                             timestep_atom.velocity = np.array(
    #                                 [float(vi) for vi in next(f).split()]
    #                             )

    #                         if (
    #                             timestep.trajectory_key
    #                             is DlpolyTrajectoryKey.CoordinateVelocityForce
    #                         ):
    #                             timestep_atom.force = np.array(
    #                                 [float(fi) for fi in next(f).split()]
    #                             )

    #                         timestep.add(timestep_atom)

    #                     if add_this_timestep:
    #                         self.add(timestep)

    #         # if end of file is reached, add the removed timesteps attribute
    #         except StopIteration:
    #             self.removed_timesteps = removed_timesteps

    @convert_to_path
    def write_to_trajectory(self, path: str = "TRAJECTORY.xyz"):
        """Writes a trajectory .xyz file from the DL POLY HISTORY file."""

        self.write(path)

    def write_final_geometry_to_xyz(self, xyz_path: Path):

        from ichor.core.files import XYZ

        xyz_inst = XYZ(xyz_path)
        xyz_inst.atoms = self[-1]
        xyz_inst.write()
