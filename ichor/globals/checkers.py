from typing import Any, List


def check_allowed(val: Any, allowed_values: List[Any]):
    if val not in allowed_values:
        raise ValueError(
            f"Value: {val} not in Allowed Values: {allowed_values}"
        )


def positive(val):
    if not val > 0:
        raise ValueError(f"Value: {val} must be > 0")


def positive_or_zero(val):
    if not val >= 0:
        raise ValueError(f"Value: {val} must be >= 0")
