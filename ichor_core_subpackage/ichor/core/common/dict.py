from typing import TypeVar, Union, MutableMapping, Any
from functools import reduce
from collections import abc
from contextlib import suppress


KT = TypeVar("KT")
VT = TypeVar("VT")


class DictionaryMergeConflict(Exception):
    pass


def merge_mutable(a, b, path=None):
    """merges b into a, modifies a"""
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_mutable(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                raise DictionaryMergeConflict(
                    f'Conflict at {".".join(path + [str(key)])}'
                )
        else:
            a[key] = b[key]
    return a


def merge(*dicts):
    """Merges dictionaries (dicts) immutably
    e.g.
        >>> {"total_energy": -76.4}, {"O1": {"iqa": -75.2}}, {"O1": {"dispersion": -1.0}}
        {"total_energy": -76.4, "O1": {"iqa": -75.2, "dispersion": -1.0}}
    """
    return reduce(merge_mutable, map(dict, dicts))


def find(key: KT, d: MutableMapping[KT, VT]) -> MutableMapping[KT, VT]:
    """Recursively searches dictionary 'd' for the given 'key'
    e.g.
        >>> find("iqa", {"energy": -76.54, "O1": {"iqa": -75.40, "q00": -0.22}, "H2": {"iqa": -0.52, "q00": 0.15}})
        {"O1": {"iqa": -75.40}, "H2": {"iqa": -0.52}}
    """
    result = {}
    if key in d.keys():
        result[key] = d[key]
    else:
        for k, v in d.items():
            if isinstance(v, MutableMapping):
                with suppress(KeyError):
                    result[k] = find(key, v)
    if not result:
        raise KeyError(f"'{key}' not found.")
    return result


def unwrap_single_entry(
    d: MutableMapping[KT, VT]
) -> Union[MutableMapping[KT, VT], VT]:
    """Unwraps the dictionary if there is only a single item in the dicitonary
    e.g.
        >>> unwrap_single_entry({"energy": -76.54})
        -76.54
        >>> unwrap_single_entry({"O1": {"iqa": -75.40})
        75.40
        >>> unwrap_single_entry({"O1": {"iqa": -75.40}, "H2": {"iqa": -0.52}})
        {"O1": -75.40, "H2": -0.52}
    """
    if len(d) > 1:
        return {
            k: unwrap_single_entry(v) if isinstance(v, MutableMapping) else v
            for k, v in d.items()
        }

    v = next(iter(d))
    return unwrap_single_entry(v) if isinstance(v, MutableMapping) else v


def unwrap_single_item(
    d: MutableMapping[KT, VT], item: KT
) -> Union[MutableMapping[KT, VT], VT]:
    """Unwraps the dictionary if the given 'item' is the only item in the dictionary
    e.g.
        >>> unwrap_single_item({"energy": -76.54}, "energy")
        -76.54
        >>> unwrap_single_item({"O1": {"iqa": -75.40}, "H2": {"iqa": -0.52}}, "iqa")
        {"O1": -75.40, "H2": -0.52}
    """
    if len(d) > 1 or item not in d.keys():
        return {
            k: unwrap_single_item(v, item)
            if isinstance(v, abc.MutableMapping)
            else v
            for k, v in d.items()
        }

    v = next(iter(d.values()))
    return (
        unwrap_single_item(v, item) if isinstance(v, abc.MutableMapping) else v
    )
