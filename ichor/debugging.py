import sys


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
