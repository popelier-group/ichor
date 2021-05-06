from typing import Iterable


def cleanup_str(str_in: str) -> str:
    return str_in.replace('"', "").replace("'", "").strip()


def join(iterable: Iterable) -> str:
    return " ".join(map(str, iterable))


def decode(binary_str: bytes) -> str:
    return binary_str.decode("ascii").strip()


def get_digits(str_in: str) -> int:
    return int("".join(c for c in str_in if c.isdigit()))
