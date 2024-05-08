import itertools
from typing import Iterable


def chunker(iterable: Iterable, size: int):
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, size))
