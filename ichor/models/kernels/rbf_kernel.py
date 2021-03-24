import numpy as np

from ichor.models.kernels.kernel import Kernel


def RBF_k(l, xi, xj):
    diff = xi - xj
    return np.exp(-np.sum(l * diff * diff))


@jit(nopython=True)
def RBF_r(l, xi, x):
    n_train = x.shape[0]
    r = np.empty((n_train, 1))
    for j in range(n_train):
        r[j] = RBF_k(l, xi, x[j])
    return r


@jit(nopython=True)
def RBF_R(l, x):
    n_train = x.shape[0]
    R = np.empty((n_train, n_train))
    for i in range(n_train):
        R[i, i] = 1.0
        for j in range(n_train):
            R[i, j] = RBF_k(l, x[i], x[j])
            R[j, i] = R[i, j]
    return R


class RBF(Kernel):
    """Implements Radial Basis Function (RBF) kernel used to calculate covariance matrix"""

    def __init__(self, lengthscale: np.array):

        self.lengthscale = lengthscale

    @property
    def params(self):
        return self.lengthscale

    def k(self, xi, xj):
        return RBF_k(self.lengthscale, np.array(xi), np.array(xj))

    def r(self, xi, x):
        return RBF_r(self.lengthscale, np.array(xi), np.array(x))

    def R(self, x):
        return RBF_R(self.lengthscale, np.array(x))
