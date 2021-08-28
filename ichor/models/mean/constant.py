import numpy as np

from ichor.models.mean.mean import Mean


class ConstantMean(Mean):
    """ A constant value that is used for the mean function. When no training data is present close to test points, covariance is low, therefore
    the predictions for the test points will be this constant mean value.
    
    :param value: A float to be used as the constant mean value
    """
    def __init__(self, value: float):
        self._value = value

    def value(self, x: np.ndarray) -> float:
        """ Returns the constant mean value."""
        return self._value

    def values(self, x: np.ndarray) -> np.ndarray:
        """ Fill an array with the constant mean value, that is of the same shape as x.shape[0] (this is the number of samples usually)
        
        :param x: A numpy array
        """
        return np.full((x.shape[0]), self._value)
