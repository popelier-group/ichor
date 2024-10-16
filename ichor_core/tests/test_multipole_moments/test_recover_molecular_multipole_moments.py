import numpy as np
from ichor.core.files import GaussianOutput, IntDirectory
from ichor.core.multipoles.dipole import get_gaussian_and_aimall_molecular_dipole
from ichor.core.multipoles.hexadecapole import (
    get_gaussian_and_aimall_molecular_hexadecapole,
)
from ichor.core.multipoles.octupole import get_gaussian_and_aimall_molecular_octupole
from ichor.core.multipoles.quadrupole import (
    get_gaussian_and_aimall_molecular_quadrupole,
)

from tests.path import get_cwd

example_dir = get_cwd(__file__) / ".." / ".." / ".." / "example_files"

gaussian_output = GaussianOutput(
    example_dir / "example_point_directory" / "WD0000.pointdir" / "WD0000.gau"
)
aimall_ints = IntDirectory(
    example_dir / "example_point_directory" / "WD0000.pointdir" / "WD0000_atomicfiles"
)


def test_recover_molecular_dipole_moment():

    gaussian, aimall_recovered = get_gaussian_and_aimall_molecular_dipole(
        gaussian_output, aimall_ints
    )

    np.testing.assert_allclose(gaussian, aimall_recovered, atol=1e-3)


def test_recover_molecular_quadrupole_moment():

    gaussian, aimall_recovered = get_gaussian_and_aimall_molecular_quadrupole(
        gaussian_output, aimall_ints
    )

    np.testing.assert_allclose(gaussian, aimall_recovered, atol=1e-3)


def test_recover_molecular_octupole_moment():

    gaussian, aimall_recovered = get_gaussian_and_aimall_molecular_octupole(
        gaussian_output, aimall_ints
    )

    np.testing.assert_allclose(gaussian, aimall_recovered, atol=1e-3)


def test_recover_molecular_hexadecapole_moment():

    gaussian, aimall_recovered = get_gaussian_and_aimall_molecular_hexadecapole(
        gaussian_output, aimall_ints
    )

    np.testing.assert_allclose(gaussian, aimall_recovered, atol=1e-2)
