from ichor.core.common.types.itypes import T
from typing import Optional

def _assert_val_optional(value: T, expected_value: Optional[T]):
    if expected_value is not None:
        assert value == expected_value