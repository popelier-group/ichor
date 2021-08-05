import builtins
import inspect
import types

_builtin_hasattr = builtins.hasattr
if not isinstance(_builtin_hasattr, types.BuiltinFunctionType):
    raise Exception("hasattr already patched by someone else!")


def hasattr(obj, name):
    return _builtin_hasattr(obj, name)


builtins.hasattr = hasattr


def called_from_hasattr():
    # Caller's caller's frame.
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code is hasattr.__code__
