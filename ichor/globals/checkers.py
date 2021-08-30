from typing import Any, List


def check_allowed(val: Any, allowed_values: List[Any]):
    """ Check that the read in setting value from config file against allowed values for that setting."""
    if val not in allowed_values:
        raise ValueError(
            f"Value: {val} not in Allowed Values: {allowed_values}"
        )


def positive(val):
    """ Check if a value of a setting read from config file is positive."""
    if not val > 0:
        raise ValueError(f"Value: {val} must be > 0")


def positive_or_zero(val):
    """ Check if a value of a setting read from config file is positive or 0."""
    if not val >= 0:
        raise ValueError(f"Value: {val} must be >= 0")
