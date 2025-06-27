from ase.io import read
from ase.optimize import BFGS
from ase.io import write
from xtb.ase.calculator import XTB

# Define the atomic structure
atoms = read("input.xyz")

# Define calculator
xtb_calc = XTB(method="GFN2-xTB",solvent="none", electronic_temperature=300, max_iterations=2048)

# Attach your external calculator
atoms.calc = xtb_calc

# Run geometry optimization using BFGS algorithm
optimizer = BFGS(atoms, trajectory='opt.traj', logfile='opt.log')
optimizer.run(fmax=0.01)  # Stop when max force < 0.01 eV/A

# Save the optimized structure
write('optimized.xyz', atoms)

# Print final energy and geometry
print("Final energy:", atoms.get_potential_energy())
print("Final positions:\n", atoms.get_positions())
print("Final forces:\n", atoms.get_forces())
