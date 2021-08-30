import numpy as np

from ichor.models.mean.mean import Mean


class ZeroMean(Mean):
    """ Implements a zero mean for the Gaussian Process. When covariance between training points and a test point is low, this means the GP will return the
    mean of the GP (in this case it is set to 0)."""
    def value(self, x: np.ndarray) -> float:
        """ Return 0 as this is a Zero Mean Gaussian Process"""
        return 0.0

    def values(self, x: np.ndarray) -> np.ndarray:
        """ Return a np array filled with zeroes that is the same shape as x.shape[0]
        
        :param x: A numpy array
        """
        return np.zeros((x.shape[0]))
