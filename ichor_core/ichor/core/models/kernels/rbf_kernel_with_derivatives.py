import numpy as np
from ichor.core.models.kernels.kernel import Kernel


class RBFKernelWithDerivatives(Kernel):
    r"""
    Implementation of the RBF kernel with derivatives, where the rbf dimensions all dimensions.

    .. note::
        Need to use kernel_instance.double() in torch implementation to get the exact same results as this,
        torch defaults to float32 for some reason.
    """

    def __init__(
        self,
        name: str,
        rbf_thetas: np.ndarray,
        rbf_dimensions: np.ndarray,
    ):

        ndims = len(rbf_dimensions)
        active_dims = np.arange(ndims)

        super().__init__(name, active_dims)
        self._rbf_thetas = rbf_thetas
        self.rbf_dimensions = rbf_dimensions

    @property
    def params(self) -> np.ndarray:
        pass

    @property
    def rbf_lengthscales(self):
        return 1.0 / (2.0 * self._rbf_thetas)

    @property
    def ndims(self):
        return len(self.active_dims)

    @property
    def lengthscale(self) -> np.ndarray:
        """Returns a 1D array of lengtshcales for both RBF and periodic which
        are ordered correctly (i.e. first 3 lengthscales are RBF ones, then it repeats RBF RBF Periodic)
        """
        l = []
        iter_rbf_dims = iter(self.rbf_lengthscales)

        for i in range(len(self.active_dims)):
            l.append(next(iter_rbf_dims))

        # needs to be 1 x ndim to be able to fit with torch implementation
        return np.array(l)[np.newaxis, ...]

    @property
    def lengthscales(self):
        return self.lengthscale

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calculates RBF covariance matrix with derivatives from two sets of points

        Args:
            :param: `x1` np.ndarray of shape m x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape n x ndimensions:
                Second matrix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The covariance matrix of shape (m*(ndim+1), n*(ndim+1))
        """
        # Get lengthscale and square it
        # gpytorch does not use already squared lengthscale for RBF kernel with gradient
        # so this is why it is needed here
        lengthscale_sq = self.lengthscale**2

        batch_shape = x1.shape[:-2]
        n1, d = x1.shape[-2:]
        n2 = x2.shape[-2]

        # this is the full matrix
        K = np.zeros((*batch_shape, n1 * (d + 1), n2 * (d + 1)), dtype=x1.dtype)

        # shape of n1 x n2 x d
        diffs = x1.reshape(*batch_shape, n1, 1, d) - x2.reshape(*batch_shape, 1, n2, d)

        # rbf part of matrix
        # shape is n1 x n2 x nrbfdims
        rbf_part = diffs[..., self.rbf_dimensions] ** 2
        rbf_part = rbf_part / np.expand_dims(
            lengthscale_sq[..., self.rbf_dimensions], -2
        )
        # sum over nrbfdims
        rbf_part = rbf_part.sum(-1) * (-0.5)

        # # 1) Kernel block
        # # directly use the already implemented RBF and PeriodicKernel methods
        K[..., :n1, :n2] = np.exp(rbf_part)

        # outer1 here is the rbf part, but name as the final variable, and use inplace operations to save memory
        # divide each dimension by the lengthscale
        outer = diffs / np.expand_dims(lengthscale_sq, -2)
        # get n1 x n2 x d tensor
        outer = np.swapaxes(outer, -1, -2)

        # get n1 x n2 * d tensor
        outer1 = outer.reshape(*batch_shape, n1, n2 * d)

        K[..., :n1, n2:] = outer1 * np.tile(K[..., :n1, :n2], d)

        outer2 = outer.swapaxes(-3, -1)  # n2 x d x n1
        outer2 = outer2.reshape(*batch_shape, n2, n1 * d)  # n2 x n1 * d
        outer2 = outer2.swapaxes(-1, -2)  # n1 * d x n2

        K[..., n1:, :n2] = -outer2 * np.tile(K[..., :n1, :n2], (d, 1))

        outer3 = np.tile(outer1, (d, 1)) * np.tile(-outer2, (1, d))

        # # 4) Hessian block kronecker for rbf part
        kp_rbf = np.kron(
            np.eye(d, dtype=x1.dtype) / lengthscale_sq,
            np.ones((n1, n2), dtype=x1.dtype),
        )

        # outer3 is already -ve
        K[..., n1:, n2:] = (kp_rbf + outer3) * np.tile(K[..., :n1, :n2], (d, d))

        # Symmetrize for stability
        if n1 == n2 and np.equal(x1, x2).all():
            K = 0.5 * (K.swapaxes(-1, -2) + K)

        # Apply a perfect shuffle permutation to match the weights ordering
        # this orderes as cov(y1, y1) cov(y1, w11) cov(y1, w12) cov(y1, w13) ... cov(y1, wij)
        # where i is the training index and j is the deriv dimension for each row
        # without this permutation the ordering is
        # cov(y1, y1) cov(y1, y2) ... cov(y1, yn) cov(y1, w11) cov(y1, w21) ... cov(y1, wn1) ...
        # cov(y1, w12) cov(y1, w22) cov(y1, w32) ... .... cov(y1, wND) where N is ntrain and D is dim
        pi1 = np.arange(n1 * (d + 1)).reshape(d + 1, n1).T.reshape((n1 * (d + 1)))
        pi2 = np.arange(n2 * (d + 1)).reshape(d + 1, n2).T.reshape((n2 * (d + 1)))
        K = K[..., pi1, :][..., :, pi2]

        return K

    def write_str(self) -> str:

        str_to_write = ""

        str_to_write += f"[kernel.{self.name}]\n"
        str_to_write += "type constant\n"
        str_to_write += f"number_of_dimensions {len(self.active_dims)}\n"
        str_to_write += f"active_dimensions {' '.join(map(str, self.active_dims+1))}\n"
        str_to_write += f"thetas {' '.join(map(str, self._rbf_thetas))}\n"

        return str_to_write

    def __repr__(self):

        lengthscales = self.lengthscales

        return f"{self.__class__.__name__}: lengthscales: {lengthscales}"
