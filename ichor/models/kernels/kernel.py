import numpy as np
from abc import ABC, abstractmethod


class Kernel(ABC):
    """ Base class for all kernels that implements dunder methods for addition or multiplication of separate kernels"""

    @property
    def params(self):
        # TODO: Convert this to error
        print("Error: Params not defined for specified kernel")
        quit()

    @abstractmethod
    def k(self):
        """ abstract method for calculating covariance matrix between two sets of vectors, needs to be implemented by child classes"""
        pass

    @abstractmethod
    def r(self):
        """ abstract method for calculating test-train covariance matrix K(X*, X) """
        pass

    @abstractmethod
    def R(self):
        """ abstract method for calculating train-train covariance matrix K(X, X) which is a symmetric square matrix """
        pass

    def __add__(self, other):
        return KernelSum(self, other)

    def __mul__(self, other):
        return KernelProd(self, other)


class KernelSum(Kernel):
    """ Kernel addition implementation"""

    def __init__(self, k1: Kernel, k2: Kernel):
        self.k1 = k1
        self.k2 = k2

    @property
    def params(self):
        return np.concatenate(self.k1.params, self.k2.params)

    def k(self, xi, xj):
        return self.k1.k(xi, xj) + self.k2.k(xi, xj)

    def r(self, xi, x):
        return self.k1.r(xi, x) + self.k2.r(xi, x)

    def R(self, x):
        return self.k1.R(x) + self.k2.R(x)


class KernelProd(Kernel):
    """ Kernel multiplication implementation"""

    def __init__(self, k1, k2):
        self.k1 = k1
        self.k2 = k2

    @property
    def params(self):
        return np.concatenate(self.k1.params, self.k2.params)

    def k(self, xi, xj):
        return self.k1.k(xi, xj) * self.k2.k(xi, xj)

    def r(self, xi, x):
        return self.k1.r(xi, x) * self.k2.r(xi, x)

    def R(self, x):
        return self.k1.R(x) * self.k2.R(x)
