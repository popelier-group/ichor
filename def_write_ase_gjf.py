from ase.atoms import Atom, Atoms
from ase.io.gaussian import write_gaussian_in

atoms = Atoms(
    [
        Atom("N", (1.30610788, -29.77550072, -0.39451506)),
        Atom("H", (0.88322943, -29.08071028, -1.14190493)),
        Atom("H", (1.46749713, -29.22282070, 0.46703669)),
        Atom("H", (2.11921902, -30.18852549, -0.75438182)),
    ]
)

print(atoms)

with open("ase_example.gjf", "w") as f:

    write_gaussian_in(f, atoms, method="b3lyp", basis="aug-cc-pvtz", mult=1, charge=0)
