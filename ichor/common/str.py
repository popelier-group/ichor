""" Useful functions which are used to manipulate a str or return a str."""

from typing import Iterable, Optional


def cleanup_str(str_in: str) -> str:
    """ Removes single and double quotes from the string, as well as any whitespace from the given string."""
    return str_in.replace('"', "").replace("'", "").strip()


def join(iterable: Iterable) -> str:
    """ Converts every element of the iterable object into a string and joins with a space. Returns the joined string."""
    return " ".join(map(str, iterable))


def decode(binary_str: Optional[bytes]) -> str:
    """ Decodes the incoming binary into ascii (which contains letters and numbers) and returns the string containing the ascii characters."""
    return binary_str.decode("ascii").strip() if binary_str else ""


def get_digits(str_in: str) -> int:
    """ Gets the digits in a string and retruns the integer number corresponding to the joined digits."""
    return int("".join(c for c in str_in if c.isdigit()))
