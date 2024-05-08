from typing import Optional

import numpy as np

from ichor.core.common.types.itypes import T


def _assert_val_optional(value: T, expected_value: Optional[T]):
    if expected_value is not None:
        assert value == expected_value


def _compare_nested_dicts(dict1, dict2):
    """Recursively compare nested dictionaries that include NumPy arrays."""
    if dict1.keys() != dict2.keys():
        return False

    for key in dict1:
        if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            if not _compare_nested_dicts(dict1[key], dict2[key]):
                return False
        elif isinstance(dict1[key], np.ndarray) and isinstance(dict2[key], np.ndarray):
            if not np.allclose(dict1[key], dict2[key]):
                return False
        else:
            if dict1[key] != dict2[key]:
                return False

    return True


__all__ = ["_assert_val_optional", "_compare_nested_dicts"]
