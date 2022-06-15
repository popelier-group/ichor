import numpy as np
from ichor.core.atoms.calculators import calculate_connectivity
from ichor.core.files import Trajectory
from tests.path import get_cwd

example_dir = get_cwd(__file__) / ""


def test_water_3000():
    expected_connectivity = np.array(
        [
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
        ]
    )
    traj = Trajectory(example_dir / "water-3000.xyz")

    for timestep in traj:
        assert np.all(
            calculate_connectivity(timestep) == expected_connectivity
        )
