import builtins
import inspect
import types

# matt_todo: maybe better for you to explain why this is needed because it is needed for a very specific case which is hard to understand.

_builtin_hasattr = builtins.hasattr
if not isinstance(_builtin_hasattr, types.BuiltinFunctionType):
    raise Exception("hasattr already patched by someone else!")


def hasattr(obj, name):
    return _builtin_hasattr(obj, name)


builtins.hasattr = hasattr


def called_from_hasattr():
    # Caller's caller's frame.
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code is hasattr.__code__  # returns True if the frame's code is the same as the code in the hasattr function above
