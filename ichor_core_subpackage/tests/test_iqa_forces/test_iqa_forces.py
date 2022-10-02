from ichor.core.files import XYZ
from ichor.core.models.models import Models
from ichor.core.models.predict_forces_for_all_atoms import predict_fflux_forces_for_all_atoms
from ichor.core.calculators import calculate_alf_atom_sequence
import numpy as np
from tests.path import get_cwd

tests_dir_path = get_cwd(__file__)

def test_assert_forces():
    xyz_inst = XYZ(f"{tests_dir_path}/starting_geom_centered_atoms.xyz")
    atoms = xyz_inst.atoms
    models = Models(f"{tests_dir_path}/models")
    SYSTEM_ALF = atoms.alf_list(calculate_alf_atom_sequence)
    forces = predict_fflux_forces_for_all_atoms(atoms, models, SYSTEM_ALF)

    true_forces  = np.array([[ 0.00825742, -0.00024052,  0.011623],
                            [-0.03068412,  0.01004581, -0.0002195],
                            [ 0.01836564, -0.0126511,  -0.00198348],
                            [ 0.00406107,  0.00284581, -0.00942002]])

    np.testing.assert_allclose(forces, true_forces, atol=1e-8)