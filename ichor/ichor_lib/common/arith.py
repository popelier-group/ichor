import math

from ichor.ichor_lib.itypes import Scalar


def order_of_magnitude(n: Scalar) -> int:
    """
    Returns the order of magnitude of n
    e.g.
    ```
    >>> order_of_magnitude(100)
    2
    >>> order_of_magnitude(0.0001)
    -4

    ```
    :param n: number to calculate order of magnitude of
    :return: order of magnitude of n
    """
    return math.floor(math.log(n, 10))
