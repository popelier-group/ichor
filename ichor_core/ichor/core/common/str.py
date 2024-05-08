""" Useful functions which are used to manipulate a str or return a str."""

from typing import Iterable, List, Optional


def cleanup_str(str_in: str) -> str:
    """Removes single and double quotes from the string,
    as well as any whitespace from the given string."""
    return str_in.replace('"', "").replace("'", "").strip()


def join(iterable: Iterable) -> str:
    """Converts every element of the iterable object into
    a string and joins with a space. Returns the joined string."""
    return " ".join(map(str, iterable))


def decode(binary_str: Optional[bytes]) -> str:
    """Decodes the incoming binary into ascii (which contains letters and numbers)
    and returns the string containing the ascii characters."""
    return binary_str.decode("ascii").strip() if binary_str else ""


def get_digits(str_in: str) -> int:
    """Gets the digits in a string and returns
    the integer number corresponding to the joined digits."""
    return int("".join(c for c in str_in if c.isdigit()))


def get_characters(str_in: str) -> str:
    """Removes the digits from a string and returns resulting string"""
    return "".join(c for c in str_in if not c.isdigit())


def split_every(s: str, n: int) -> List[str]:
    """
    split string s every n characters
    :param s: string to split
    :param n: n to split s by
    :return: list of strings split every n characters
    """
    return [s[i : i + n] for i in range(0, len(s), n)]


def split_by(
    s: str, n: List[int], strip: bool = True, return_remainder: bool = True
) -> List[str]:
    """
    split s by integer list n
    e.g.
    ```python
    >>> split_by('abcdefg', [1, 2, 3])
    ['a', 'bc', 'def', 'g']
    >>> split_by('abcdefg', [1, 2, 3], return_remainder=False)
    ['a', 'bc', 'def']
    ```
    :param s: string to split
    :param n: list of integers to split s by
    :return: list of strings split from original
    """
    new_s = []
    m = 0
    for ni in n:
        if m + ni >= len(s):
            ni = len(s) - m
        new_si = s[m : m + ni]
        if strip:
            new_si = new_si.strip()
        new_s += [new_si]
        m += ni
    new_s += ["" for _ in range(len(n) - len(new_s))]
    if return_remainder:
        if m < len(s):
            new_s += [s[m:]]
    return new_s


def in_sensitive(value: str, lst: List[str]) -> bool:
    """
    Case insensitive 'in'
    :param value: value to search list for
    :param lst: list of strings to search value in
    :return: boolean based on whether value is in lst ignoring case
    """
    return value.lower() in [i.lower() for i in lst]
