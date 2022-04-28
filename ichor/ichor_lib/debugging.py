import sys
import time
from functools import wraps

from ichor_lib.itypes import F, T


def printq(*args) -> None:
    """
    Useful function to use while debugging on remote servers, simpy acts as a normal print statement
    before exiting directly afterwards

    :param args:
    :return: None

    Note: only to be used for debugging while developing should not be used for production
    """
    print(*args)
    sys.exit()


def timer(f: F) -> F:
    """
    Times execution time of function f and prints to stdout

    :param f: Function to time
    :return: Return value of function f
    """

    @wraps(f)
    def wrap(*args, **kwargs) -> T:
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        print(f"{f.__name__} function took {time2 - time1:.3f} s")
        return ret

    return wrap
