import math


def count_digits(n: int) -> int:
    """Count number of digits in n"""
    return math.floor(math.log(n, 10) + 1)
