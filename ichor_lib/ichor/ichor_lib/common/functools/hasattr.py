import builtins
import inspect
import types

"""
    When using hasattr in ichor, it may be preferrable to use
    
    ```python
    from ichor_lib.common.functools import hasattr
    ```
        
    This hasattr overrides the builtin hasattr so that if hasattr is called from a hasattr statement,
    it can be seen using inspect.current_frame(). This is because the builtin hasattr is written in C
    and therefore cannot be seen by inspect and we therefore cannot avoid this possible infinite recurssive
    loop.
    
    This is of great importance when wanting to use hasattr in a __getattr__ method as hasattr calls
    __getattr__ and an infinite loop is began, with this method one can use the following:
    
    ```python
    from ichor_lib.common.functools import hasattr, called_from_hasattr
    
    ...
    
    class MyClass:
        ...
        def __getattr__(self, item):
            ...
            if not called_from_hasattr() and hasattr(item):
                ...
    ```
    
    Note the order of `called_from_hasattr` and `hasattr`
    
    This is primarily used in the `PathObject` class for lazy reading of attributes from the file on disk
    but is general purpose code for use anywhere
"""

_builtin_hasattr = builtins.hasattr
if not isinstance(_builtin_hasattr, types.BuiltinFunctionType):
    raise Exception("hasattr already patched by someone else!")


def hasattr(obj, name):
    return _builtin_hasattr(obj, name)


builtins.hasattr = hasattr


def called_from_hasattr():
    # Caller's caller's frame.
    frame = inspect.currentframe().f_back.f_back
    return (
        frame.f_code is hasattr.__code__
    )  # returns True if the frame's code is the same as the code in the hasattr function above
