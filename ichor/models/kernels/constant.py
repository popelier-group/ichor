from typing import IO, Optional

import numpy as np

from ichor.models.kernels.kernel import Kernel


class ConstantKernel(Kernel):
    """Implements constant kernel, which scales by a constant factor when used in a kernel product or
    modifies the mean of the Gaussian process when used in a kernel sum"""

    def __init__(
        self, name: str, value: float, active_dims: Optional[np.ndarray]
    ):
        super().__init__(self, name, active_dims)
        self.value = value

    @property
    def params(self):
        return np.array([self.value])

    def k(self, xi, xj):
        return self.value

    def r(self, xi, x):
        return np.full((len(x), 1), self.value)

    def R(self, x):
        return np.full((len(x), len(x)), self.value)

    def write(self, f: IO):
        f.write(f"[kernel.{self.name}]\n")
        f.write("type constant\n")
        f.write(f"number_of_dimensions {len(self.active_dims)}\n")
        f.write(f"active_dimensions {' '.join(map(str, self.active_dims))}\n")
        f.write(f"value {self.value}\n")
