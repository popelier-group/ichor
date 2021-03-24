import numpy as np

from .kernel import Kernel


@jit(nopython=True)
def RBFCyclic_k(l, xi, xj):
    diff = xi - xj
    # Had to do list comprehension workaround to get numba to compile
    mask = (np.array([x for x in range(diff.shape[0])]) + 1) % 3 == 0
    diff[mask] = (diff[mask] + np.pi) % (2 * np.pi) - np.pi
    return np.exp(-np.sum(l * diff * diff))


@jit(nopython=True)
def RBFCyclic_r(l, xi, x):
    n_train = x.shape[0]
    r = np.empty((n_train, 1))
    for j in range(n_train):
        r[j] = RBFCyclic_k(l, xi, x[j])
    return r


@jit(nopython=True)
def RBFCyclic_R(l, x):
    n_train = x.shape[0]
    R = np.empty((n_train, n_train))
    for i in range(n_train):
        R[i, i] = 1.0
        for j in range(n_train):
            R[i, j] = RBFCyclic_k(l, x[i], x[j])
            R[j, i] = R[i, j]
    return R


@jit(nopython=True)
def RBFCyclicStandardised_k(l, xstd, xi, xj):
    diff = xi - xj
    # Had to do list comprehension workaround to get numba to compile
    mask = (np.array([x for x in range(diff.shape[0])]) + 1) % 3 == 0
    diff[mask] = (diff[mask] + np.pi / xstd[mask]) % (
        2 * np.pi / xstd[mask]
    ) - np.pi / xstd[mask]
    return np.exp(-np.sum(l * diff * diff))


@jit(nopython=True)
def RBFCyclicStandardised_r(l, xstd, xi, x):
    n_train = x.shape[0]
    r = np.empty((n_train, 1))
    for j in range(n_train):
        r[j] = RBFCyclicStandardised_k(l, xstd, xi, x[j])
    return r


@jit(nopython=True)
def RBFCyclicStandardised_R(l, xstd, x):
    n_train = x.shape[0]
    R = np.empty((n_train, n_train))
    for i in range(n_train):
        R[i, i] = 1.0
        for j in range(n_train):
            R[i, j] = RBFCyclicStandardised_k(l, xstd, x[i], x[j])
            R[j, i] = R[i, j]
    return R


class RBFCyclic(Kernel):
    def __init__(self, lengthscale, xstd=None):
        self.lengthscale = np.array(lengthscale)
        self.xstd = xstd

    @property
    def params(self):
        return self.lengthscale

    def k(self, xi, xj):
        if self.xstd is None:
            return RBFCyclic_k(self.lengthscale, np.array(xi), np.array(xj))
        else:
            return RBFCyclicStandardised_k(
                self.lengthscale,
                np.array(self.xstd),
                np.array(xi),
                np.array(xj),
            )

    def r(self, xi, x):
        if self.xstd is None:
            return RBFCyclic_r(self.lengthscale, np.array(xi), np.array(x))
        else:
            return RBFCyclicStandardised_r(
                self.lengthscale,
                np.array(self.xstd),
                np.array(xi),
                np.array(x),
            )

    def R(self, x):
        if self.xstd is None:
            return RBFCyclic_R(self.lengthscale, np.array(x))
        else:
            return RBFCyclicStandardised_R(
                self.lengthscale, np.array(self.xstd), np.array(x)
            )
