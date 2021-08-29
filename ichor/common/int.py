import math


def count_digits(n: int) -> int:
    """Count number of digits in n, see https://stackoverflow.com/q/24176789/11699003 for example/explanation"""
    return math.floor(math.log(n, 10) + 1)
