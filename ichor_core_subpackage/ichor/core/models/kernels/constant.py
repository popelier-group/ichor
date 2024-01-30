from typing import Optional

import numpy as np
from ichor.core.models.kernels.kernel import Kernel


class ConstantKernel(Kernel):
    """Implements constant kernel, which scales by a constant factor when used in a kernel product or
    modifies the mean of the Gaussian process when used in a kernel sum"""

    def __init__(self, name: str, value: float, active_dims: Optional[np.ndarray]):
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

    def write_str(self) -> str:

        str_to_wrte = ""

        str_to_wrte += f"[kernel.{self.name}]\n"
        str_to_wrte += "type constant\n"
        str_to_wrte += f"number_of_dimensions {len(self.active_dims)}\n"
        str_to_wrte += f"active_dimensions {' '.join(map(str, self.active_dims+1))}\n"
        str_to_wrte += f"value {self.value}\n"

        return str_to_wrte
