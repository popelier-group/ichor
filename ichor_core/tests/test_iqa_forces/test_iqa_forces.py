import numpy as np
from ichor.core.calculators import calculate_alf_atom_sequence
from ichor.core.files import XYZ
from ichor.core.models.models import Models
from ichor.core.models.predict_forces_for_all_atoms import (
    predict_fflux_forces_for_all_atoms,
)

from tests.path import get_cwd

example_dir = get_cwd(__file__) / ".." / ".." / ".." / "example_files"


def test_assert_forces():
    xyz_inst = XYZ(example_dir / "xyz" / "AMMONIA-1000.xyz")
    atoms = xyz_inst.atoms
    models = Models(example_dir / "models")
    SYSTEM_ALF = atoms.alf_list(calculate_alf_atom_sequence)
    forces = predict_fflux_forces_for_all_atoms(atoms, models, SYSTEM_ALF)

    true_forces = np.array(
        [
            [0.06514612, 0.02700218, -0.12684424],
            [-0.0331026, -0.00729641, 0.04316535],
            [-0.01706029, -0.0419113, 0.0348614],
            [-0.01498323, 0.02220553, 0.04881749],
        ]
    )

    np.testing.assert_allclose(forces, true_forces, atol=1e-8)
