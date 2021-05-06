from ichor.files.trajectory import Trajectory
from ichor.atoms import Atoms, Atom


class DlpolyHistory(Trajectory):
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
        if fname is None:
            fname = self.path.parent / Path("TRAJECTORY.xyz")
        super().write(fname=fname)

    def write_to_trajectory(self):
        self.write()
