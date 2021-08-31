from typing import Any


class MutableValue:
    """
    Allows for immutable values to be used as mutable values

    If using regular immutable types such as `int`s
    ```python
    >>> a = 2
    >>> b = a
    >>> a = 3
    >>> a
    3
    >>> b
    2
    ```

    The same example with the MutableValue
    ```python
    >>> a = MutableValue(2)
    >>> b = a
    >>> a.value = 3
    >>> a.value
    3
    >>> b.value
    3
    ```

    There may be a better way to implement this with descriptors but this works for now and is used
    by auto_run for modifying function arguments while iterating
    """
    def __init__(self, value: Any):
        self.value = value
