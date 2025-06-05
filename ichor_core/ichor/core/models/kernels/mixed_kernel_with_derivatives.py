import math

import numpy as np
from ichor.core.models.kernels.kernel import Kernel


class MixedKernelWithDerivatives(Kernel):
    r"""
    Implementation of the mixed kernel, where the rbf dimensions are used for non-cyclic dimensions
    and the periodic kernel is used for cyclic dimensions (phi dimensions).

    Also adds first and second derivatives of the mixed kernel which are used to train on the total
    system energy with gradient information.

    The data is assumed to be uscaled, i.e. the original data. The period length array is set for all
    the dimensions even though it is only used for the periodic dimensions to vectorize the operations.
    The period length is set to be 2 * math.pi for all dimensions, as this is the optimal value for
    the ALF phi features.

    .. note::
        Need to use kernel_instance.double() in torch implementation to get the exact same results as this,
        torch defaults to float32 for some reason.

        Also, unlike the torch version, there is no need to permute the rows and columns of the
        covariance matrix because the weights vector that is in the .model files with
        gradient information is written to be in the order of all weights for energies (alpha)
        followed by all weights for derivatives (beta) instead.
    """

    def __init__(
        self,
        name: str,
        rbf_thetas: np.ndarray,
        periodic_thetas: np.ndarray,
        rbf_dimensions: np.ndarray,
        periodic_dimensions: np.ndarray,
    ):

        ndims = len(rbf_dimensions) + len(periodic_dimensions)
        active_dims = np.arange(ndims)

        super().__init__(name, active_dims)
        self._rbf_thetas = rbf_thetas
        self._periodic_thetas = periodic_thetas
        # needs to be 1 x ndim to be able to fit with torch implementation
        self.period_length = (np.ones(ndims) * (2 * math.pi))[np.newaxis, ...]

        self.rbf_dimensions = rbf_dimensions
        self.periodic_dimensions = periodic_dimensions

    @property
    def params(self) -> np.ndarray:
        pass

    @property
    def rbf_lengthscales(self):
        return 1.0 / (2.0 * self._rbf_thetas)

    @property
    def periodic_lengthscales(self):
        """Note that the lengthscales are already squared for the periodic kernel. But still,
        thetas are defined to be 1/(2l). (where l here is the already squared true lengthscale)
        """
        return 1.0 / (2.0 * self._periodic_thetas)

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
        iter_periodic_lengthscales = iter(self.periodic_lengthscales)

        for i in range(len(self.active_dims)):
            if (i + 1) % 3 == 0 and i != 2:
                l.append(next(iter_periodic_lengthscales))
            else:
                l.append(next(iter_rbf_dims))

        # needs to be 1 x ndim to be able to fit with torch implementation
        return np.array(l)[np.newaxis, ...]

    @property
    def lengthscales(self):
        return self.lengthscale

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calculates mixed covariance matrix(RBF and periodic)
         with derivatives from two sets of points

        Args:
            :param: `x1` np.ndarray of shape m x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape n x ndimensions:
                Second matrix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The covariance matrix of shape (m*(ndim+1), n*(ndim+1))
        """
        # Get lengthscale
        lengthscale = self.lengthscale

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
        rbf_part = rbf_part / np.expand_dims(lengthscale[..., self.rbf_dimensions], -2)
        # sum over nrbfdims
        rbf_part = rbf_part.sum(-1) * (-0.5)

        # # shape is n1 x n2 x nperiodic
        periodic_part = diffs[..., self.periodic_dimensions] * (
            np.expand_dims(
                math.pi / self.period_length[..., self.periodic_dimensions], -2
            )
        )
        periodic_part = np.sin(periodic_part) ** (2.0)
        periodic_part = np.divide(
            periodic_part,
            np.expand_dims(lengthscale[..., self.periodic_dimensions], -2),
        ).sum(-1) * (-2.0)

        # # 1) Kernel block
        # # directly use the already implemented RBF and PeriodicKernel methods
        K[..., :n1, :n2] = np.exp(rbf_part + periodic_part)

        # Form all possible rank-1 products for the gradient and Hessian blocks
        # rbf dx_i^n first

        periodic_dims_zeros_ones_tensor = np.array(
            [[1 if i in self.periodic_dimensions else 0 for i in range(d)]],
            dtype=x1.dtype,
        )
        rbf_dims_zeros_ones_tensor = np.array(
            [[1 if i in self.rbf_dimensions else 0 for i in range(d)]], dtype=x1.dtype
        )
        # possibly transform this kron back into a n1 x n2 x d matrix
        periodic_mask_dx_i_n = np.kron(
            periodic_dims_zeros_ones_tensor,
            np.ones((*batch_shape, n1, n2), dtype=x1.dtype),
        )
        rbf_mask_dx_i_n = np.kron(
            rbf_dims_zeros_ones_tensor, np.ones((*batch_shape, n1, n2), dtype=x1.dtype)
        )

        # outer1 here is the rbf part, but name as the final variable, and use inplace operations to save memory
        # divide each dimension by the lengthscale
        outer1 = diffs / np.expand_dims(self.lengthscale, -2)
        # get n1 x n2 x d tensor
        outer1 = np.swapaxes(outer1, -1, -2)

        # get n1 x n2 * d tensor
        outer1 = outer1.reshape(*batch_shape, n1, n2 * d)
        # multiply by mask so that periodic dimensions are 0
        outer1 *= rbf_mask_dx_i_n

        outer_topright_periodic = diffs * (
            ((2 * math.pi) / np.expand_dims(self.period_length, -2))
        )
        outer_topright_periodic = np.sin(outer_topright_periodic) * (
            2
            * math.pi
            / (
                np.expand_dims(self.lengthscale, -2)
                * np.expand_dims(self.period_length, -2)
            )
        )
        outer_topright_periodic = np.swapaxes(outer_topright_periodic, -1, -2)
        outer_topright_periodic = outer_topright_periodic.reshape(
            *batch_shape, n1, n2 * d
        )
        outer_topright_periodic = outer_topright_periodic * periodic_mask_dx_i_n

        outer1 += outer_topright_periodic

        K[..., :n1, n2:] = outer1 * np.tile(K[..., :n1, :n2], d)

        # todo: implemt this as n1 x n2 x d directly and to work on the distance matrix, that will save some space
        periodic_mask_dx_j_m = np.kron(
            periodic_dims_zeros_ones_tensor,
            np.ones((*batch_shape, n2, n1), dtype=x1.dtype),
        ).swapaxes(-2, -1)
        rbf_mask_dx_j_m = np.kron(
            rbf_dims_zeros_ones_tensor, np.ones((*batch_shape, n2, n1), dtype=x1.dtype)
        ).swapaxes(-2, -1)

        # save some memory by naming outer_bottomleft_rbf as outer2
        # and use inplace operations
        outer2 = diffs / np.expand_dims(self.lengthscale, -2)  # n1 x n2 x d
        outer2 = np.swapaxes(outer2, -1, -2)  # n1 x d x n2
        outer2 = outer2.swapaxes(-3, -1)  # n2 x d x n1
        outer2 = outer2.reshape(*batch_shape, n2, n1 * d)  # n2 x n1 * d
        outer2 = outer2.swapaxes(-1, -2)  # n1 * d x n2
        outer2 *= rbf_mask_dx_j_m  # n1 * d x n2

        outer_bottomleft_periodic = diffs * (
            ((2 * math.pi) / np.expand_dims(self.period_length, -2))
        )  # n1 x n2 x d
        outer_bottomleft_periodic = np.sin(outer_bottomleft_periodic) * (
            2
            * math.pi
            / (
                np.expand_dims(self.lengthscale, -2)
                * np.expand_dims(self.period_length, -2)
            )
        )
        outer_bottomleft_periodic = np.swapaxes(
            outer_bottomleft_periodic, -1, -2
        )  # n1 x d x n2
        outer_bottomleft_periodic = outer_bottomleft_periodic.swapaxes(
            -3, -1
        )  # n2 x d x n1
        outer_bottomleft_periodic = outer_bottomleft_periodic.reshape(
            *batch_shape, n2, n1 * d
        )
        outer_bottomleft_periodic = outer_bottomleft_periodic.swapaxes(-2, -1)
        outer_bottomleft_periodic = outer_bottomleft_periodic * periodic_mask_dx_j_m

        outer2 += outer_bottomleft_periodic

        K[..., n1:, :n2] = -outer2 * np.tile(K[..., :n1, :n2], (d, 1))

        # make mask arrays for dxjm_dxin part of matrix.
        rbf_mask_dxjm_dxin = np.tile(rbf_mask_dx_i_n, (d, 1)) * np.tile(
            rbf_mask_dx_j_m, d
        )
        periodic_mask_dxjm_dxin = np.tile(periodic_mask_dx_i_n, (d, 1)) * np.tile(
            periodic_mask_dx_j_m, d
        )

        # make mask for elements where both rbf and periodic derivatives are needed
        mask_i_P_j_R = (
            np.tile(rbf_mask_dx_i_n, (d, 1)) * np.tile(periodic_mask_dx_j_m, (1, d))
        ) + (np.tile(periodic_mask_dx_i_n, (d, 1)) * np.tile(rbf_mask_dx_j_m, (1, d)))

        outer3 = np.tile(outer1, (d, 1)) * np.tile(-outer2, (1, d))

        # # 4) Hessian block kronecker for rbf part
        kp_rbf = np.kron(
            np.eye(d, dtype=x1.dtype) / self.lengthscale,
            np.ones((n1, n2), dtype=x1.dtype),
        )

        # # 4) Hessian block for periodic part
        kp_periodic = np.kron(
            np.eye(d, dtype=x1.dtype) / self.period_length,
            np.ones((n1, n2), dtype=x1.dtype),
        )

        periodic_kp_outer3 = diffs * (
            (2.0 * math.pi) / np.expand_dims(self.period_length, -2)
        )
        periodic_kp_outer3 = (
            (4.0 * math.pi**2)
            / (
                np.expand_dims(self.period_length, -2)
                * np.expand_dims(self.lengthscale, -2)
            )
        ) * np.cos(periodic_kp_outer3)
        periodic_kp_outer3 = np.swapaxes(periodic_kp_outer3, -1, -2)
        periodic_kp_outer3 = kp_periodic * np.tile(
            periodic_kp_outer3.reshape(*batch_shape, n1, n2 * d), (d, 1)
        )

        # from matplotlib import pyplot as plt
        # plt.matshow(mask_i_P_j_R.detach().numpy())
        # plt.show()

        mixed_part3 = outer3 * mask_i_P_j_R
        mixed_part3 += (kp_rbf + outer3) * rbf_mask_dxjm_dxin
        mixed_part3 += (periodic_kp_outer3 + outer3) * periodic_mask_dxjm_dxin

        K[..., n1:, n2:] = mixed_part3 * np.tile(K[..., :n1, :n2], (d, d))

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
        str_to_write += (
            f"active_dimensions {' '.join(map(str, self.active_dims + 1))}\n"
        )
        str_to_write += f"thetas {' '.join(map(str, self._thetas))}\n"

        return str_to_write

    def __repr__(self):

        lengthscales = self.lengthscales

        return f"{self.__class__.__name__}: lengthscales: {lengthscales}"
