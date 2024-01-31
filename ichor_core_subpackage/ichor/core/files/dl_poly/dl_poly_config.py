from pathlib import Path
from typing import Union

from ichor.core.files.file import WriteFile


class DlPolyConfig(WriteFile):
    """Write out a DLPoly CONFIG file. The name of the file needs to be CONFIG,  so DL POLY knows to use it.

    :param system_name: the name of the chemical system
    :param trajectory: a Trajectory instance containing the geometries that are going to be written to
        the CONFIG file. Each timestep in the trajectory is an Atoms instance.
    :param path: The path to the CONFIG file, defaults to Path('CONFIG')
    :param cell_size: The size of the box, float
    :param comment line: The very first line in the CONFIG file.
        Must be below 72 characters

        .. note::
            ALL of the timesteps in the Trajectory will be written to one
            CONFIG file. Each timestep groups geometries which should be
            represented by a GP model. For example, if each timestep is
            only one molecule, then it means it is a monomer model and the
            labels of the atoms in the CONFIG will show that. If each timestep
            is two molecules, it means it is a dimer model, so then the
            labels in the CONFIG file will make sure that two molecules
            which should be represented by one GP model have the correct atom labeling
            in the CONFIG file.
    """

    def __init__(
        self,
        system_name: str,
        trajectory: "Trajectory",  # noqa F821
        path: Union[Path, str] = Path("CONFIG"),
        cell_size: float = 50.0,
        comment_line="Frame :         1\n",
    ):

        super().__init__(path)
        self.system_name = system_name
        self.trajectory = trajectory
        self.cell_size = float(cell_size)
        self.comment_line = comment_line

    # TODO: implement reading for dlpoly config file
    # def _read_file(self):
    #     ...

    def _write_file(self, path: Path, vmd_compatible=False):

        write_str = ""

        write_str += self.comment_line
        # see dlpoly manual 4 for settings, VMD needs to have the third optional number
        # which is the total number of particles in the system
        # (the number of timesteps * the number of atoms in one timestep)
        if vmd_compatible:
            write_str += f"0  1  {len(self.trajectory) * len(self.trajectory[0])}\n"
        else:
            write_str += "0  1\n"  # PBC Solution to temporary problem
        write_str += f"{self.cell_size} 0.0 0.0\n"
        write_str += f"0.0 {self.cell_size} 0.0\n"
        write_str += f"0.0 0.0 {self.cell_size}\n"
        total_atoms_counter = 1

        if vmd_compatible:
            for timestep in self.trajectory:
                for atom in timestep:
                    write_str += f"{atom.type}  {total_atoms_counter}\n"
                    write_str += f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n"
                    total_atoms_counter += 1
        # if CONFIG is going to be used in FFLUX, then add the index of the atoms.
        # This indicates the model file that is going to be used for that atom.
        else:
            for timestep in self.trajectory:
                for atom in timestep:
                    write_str += f"{atom.type}  {total_atoms_counter}  {self.system_name}_{atom.type}{atom.index}\n"
                    write_str += f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n"
                    total_atoms_counter += 1

        return write_str
