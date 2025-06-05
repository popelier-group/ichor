from typing import Optional

import numpy as np
from ichor.core.common.functools import cached_property
from ichor.core.models.kernels.kernel import Kernel


class RBFCyclic(Kernel):

    # TODO: figure out a good way to say if training data is standardized,
    # normalized, etc. because this kernel is affected by data preprocessing

    r"""
    Implemtation of Radial Basis Function (RBF) kernel with cyclic feature correction for phi angle feature

    .. note::
        Cyclic correction is applied only for our phi angles (phi is the azimuthal angle measured in the xy plane).

        If we have unstandardized(original) features, we have to apply this correction only
        when the distance between two phi angles is greater than pi

    .. math::

        \phi_1 - \phi_2 = \left \{
        \begin{aligned}
        &\phi_1 - \phi_2, && \text{if}\ \phi_1 - \phi_2 \leq \pi \\
        & 2\pi - (\phi_1 - \phi_2), && \text{if}\ (\phi_1 - \phi_2) \geq \pi
        \end{aligned} \right \}

    If we have standardized features (where we have subtracted the
    feature mean and divided by the feature standard deviation), we have to apply a correction
    only when the distance is greater than pi/sigma where sigma is the standard deviation of
    the particular feature in the training data.

    .. math::

        \hat \phi_1 - \hat \phi_2 = \left \{
        \begin{aligned}
        &\hat \phi_1 - \hat \phi_2, && \text{if}\ \hat \phi_1 - \hat \phi_2 \leq \frac{\pi}{\sigma} \\
        & \frac{2\pi}{\sigma} - (\hat \phi_1 - \hat \phi_2),
        && \text{if}\ (\hat \phi_1 - \hat \phi_2) \geq \frac{\pi}{\sigma}
        \end{aligned} \right \}

    """

    def __init__(
        self,
        name: str,
        thetas: np.ndarray,
        active_dims: Optional[np.ndarray] = None,
    ):
        """
        Args:
            :param: `lengthscale` np.ndarray of shape ndimensions (1D array):
                array of lengthscales. We are using a separate lengthscale for each feature(dimension).
            :param: optional, `train_x_std` np.ndarray of shape ndimensions (1D array):
                if training/test data is standardized, then `train_x_std` has to be provided.
                This array contains the standard
                deviations for each feature, calculated from the training set points.
        """
        super().__init__(name, active_dims)
        self._thetas = thetas  # np.power(1/(2.0 * lengthscale), 2)

    @property
    def params(self):
        return self._thetas

    @cached_property
    def mask(self):
        return np.arange(2, len(self._thetas), 3)

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """Calcualtes cyclic RBF covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The cyclic RBF covariance matrix matrix of shape (n, m)
        """
        diff = x2[np.newaxis, :, self.active_dims] - x1[:, np.newaxis, self.active_dims]
        diff[:, :, self.mask] = (diff[:, :, self.mask] + np.pi) % (2 * np.pi) - np.pi
        diff *= diff
        diff *= self._thetas
        return np.exp(-np.sum(diff, axis=2))

    def write_str(self) -> str:

        str_to_write = ""

        str_to_write += f"[kernel.{self.name}]\n"
        str_to_write += "type rbf-cyclic\n"
        str_to_write += f"number_of_dimensions {len(self.active_dims)}\n"
        str_to_write += (
            f"active_dimensions {' '.join(map(str, self.active_dims + 1))}\n"
        )
        str_to_write += f"thetas {' '.join(map(str, self._thetas))}\n"

        return str_to_write

    def __repr__(self):
        return f"RBFCyclic({self._thetas})"
