from ichor.atoms import Atom, Atoms
from ichor.files.trajectory import Trajectory


class DlpolyHistory(Trajectory):
    """ Wraps around a DL POLY History file, which just contains timesteps 
    with different molecular configurations. Essentially the same contents as a
    .xyz trajectory file, but in a different format."""

    # overload the Trajectory _read_file method because the formatting of the history file is different
    def _read_file(self):
        with open(self.path, "r") as f:
            for line in f:
                if line.startswith("timestep"):
                    natoms = int(line.split()[2])
                    line = next(f)  # x unit vector
                    line = next(f)  # y unit vector
                    line = next(f)  # z unit vector

                    atoms = Atoms()
                    while len(atoms) < natoms:
                        line = next(f)  # Atom Line
                        atom_type = line.split()[0]
                        line = next(f)  # Coordinate Line
                        x, y, z = line.split()
                        atoms.add(Atom(atom_type, x, y, z))
                    self.add(atoms)

    def write(self, fname=None):
        """ Writes a trajectory .xyz file from the DL POLY History file."""
        # matt_todo: Path() is not needed here
        if fname is None:
            fname = self.path.parent / Path("TRAJECTORY.xyz")
        super().write(fname=fname)

    def write_to_trajectory(self) -> None:
        """ See the `DlpolyHistory` `write` method which writes a .xyz trajectory
        from a DL POLY History File."""
        self.write()
