import numpy as np
from ichor.core.atoms.calculators import calculate_connectivity
from ichor.core.files import Trajectory
from tests.path import get_cwd
from ichor.core.atoms import Atoms
import pytest

example_dir = get_cwd(__file__) / "example_geometries"


water_connectivity = np.array(
        [
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
        ]
    )


@pytest.mark.parametrize('timestep', [t for t in Trajectory(example_dir / "water-3000.xyz")])
def test_water_3000_implicit(timestep: Atoms):
    np.testing.assert_equal(timestep.connectivity, water_connectivity)


# def test_water_3000():
#     traj = 

#     for timestep in traj:
#         np.testing.assert_equal(calculate_connectivity(timestep), expected_connectivity)
