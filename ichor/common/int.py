import numpy as np


def count_digits(n: int) -> int:
    """Count number of digits in n"""
    return np.floor(np.log(n, 10) + 1)
