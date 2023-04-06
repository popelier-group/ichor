from typing import Any, Optional, Type


def try_convert(inp: Any, ty: Type, default: Optional[Type]) -> Type:
    """
    Tries to convert input to ty, if it fails and a default is specified,
    the default value is returned otherwise the original ValueError is raised
    :param inp: input to convert to ty
    :param default: optional ty to return in case inp fails
    :return: converted ty
    :raises: ValueError if ty conversion fails and no default is specified
    """
    try:
        return ty(inp)
    except ValueError as e:
        if default is not None:
            return default
        raise e


def try_int(inp: Any, default: Optional[int] = None) -> int:
    """
    Tries to convert input to integer, if it fails and a default is specified,
    the default value is returned otherwise the original ValueError is raised
    :param inp: input to convert to integer
    :param default: optional integer to return in case inp fails
    :return: converted integer
    :raises: ValueError if int conversion fails and no default is specified
    """
    return try_convert(inp, int, default=default)


def try_float(inp: Any, default: Optional[float] = None) -> float:
    """
    Tries to convert input to float, if it fails and a default is specified,
    the default value is returned otherwise the original ValueError is raised
    :param inp: input to convert to float
    :param default: optional float to return in case inp fails
    :return: converted float
    :raises: ValueError if float conversion fails and no default is specified
    """
    return try_convert(inp, float, default=default)
