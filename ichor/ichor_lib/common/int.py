import math


def count_digits(n: int) -> int:
    """Count number of digits in n, see https://stackoverflow.com/q/24176789/11699003 for example/explanation"""
    return math.floor(math.log(n, 10) + 1)


def truncate(n: int, nbits: int = 32) -> int:
    """
    truncates an integer to the specified number of bits

    :param n: integer to truncate
    :param nbits: number of bits to truncate the integer to
    :return: truncated integer
    """
    return n & (1 << nbits) - 1
