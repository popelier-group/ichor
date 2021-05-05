import numpy as np

from .kernel import Kernel


class Constant(Kernel):

    """ Implements constant kernel, which scales by a constant factor when used in a kernel product or
    modifies the mean of the Gaussian process when used in a kernel sum"""

    def __init__(self, value):
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


# @jit(nopython=True)
# def cyclic_cdist(xa, xb):
#     xm = xa.shape[0]
#     xn = xb.shape[0]
#     result = np.empty((xm, xn))
#     for i in range(xm):
#         for j in range(xn):
#             diff = xa[i] - xb[j]
#             mask = (np.array([x for x in range(diff.shape[0])]) + 1) % 3 == 0
#             diff[mask] = (diff[mask] + np.pi) % (2 * np.pi) - np.pi
#             result[i, j] = np.sqrt(np.sum(diff * diff))
#     return result
#
#
# @jit(nopython=True)
# def standardised_cyclic_cdist(xa, xb, xstd):
#     xm = xa.shape[0]
#     xn = xb.shape[0]
#     result = np.empty((xm, xn))
#     for i in range(xm):
#         for j in range(xn):
#             diff = xa[i] - xb[j]
#             mask = (np.array([x for x in range(diff.shape[0])]) + 1) % 3 == 0
#             diff[mask] = (diff[mask] + np.pi / xstd[mask]) % (
#                 2 * np.pi / xstd[mask]
#             ) - np.pi / xstd[mask]
#             result[i, j] = np.sqrt(np.sum(diff * diff))
#     return result
