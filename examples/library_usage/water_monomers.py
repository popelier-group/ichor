import numpy as np


def to_radians(a):
    return a * np.pi/180


def to_degrees(a):

    return (a * 180) / np.pi


atom_order = ["O", "H", "H"]
traj_output = "WATER.xyz"
ntimesteps = 5000

# Water monomer parameters
bond_min = 0.8
bond_max = 1.2
angle_min = to_radians(120)
angle_max = to_radians(120)


def rand(mn, mx):
    return mn+(mx-mn)*np.random.rand()


def internal_to_cartesian(ic):
    print(ic, to_degrees(ic[2]))
    return np.array([[                0.0,                 0.0, 0.0],
                     [              ic[0],                 0.0, 0.0],
                     [ic[1]*np.cos(ic[2]), ic[1]*np.sin(ic[2]), 0.0]])


def gen_water():
    return internal_to_cartesian([
                rand(bond_min, bond_max),
                rand(bond_min, bond_max),
                rand(angle_min, angle_max),
            ])

def write_to_traj(timesteps):
    with open(traj_output, "w") as f:
        for timestep in timesteps:
            f.write(f" {len(timestep)}\n\n")
            for i, atom in enumerate(timestep):
                f.write(f"{atom_order[i]} {atom[0]} {atom[1]} {atom[2]}\n")


if __name__ == "__main__":
    traj = [gen_water() for _ in range(ntimesteps)]
    write_to_traj(traj)