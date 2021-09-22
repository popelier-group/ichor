import numpy as np


def mag(x: np.ndarray) -> float:
    """
    Calculates the magnitude of vector x
    :param x: vector of length n
    :return: the magnitude of vector x as float
    """
    return np.sqrt(x.dot(x))
