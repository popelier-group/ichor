"""
lazy - Decorators and utilities for lazy evaluation in Python
Alberto Bertogli (albertito@blitiri.com.ar)
"""


class _LazyWrapper:
    """Lazy wrapper class for the decorator defined below.
    It's closely related so don't use it.

    We don't use a new-style class, otherwise we would have to implement
    stub methods for __getattribute__, __hash__ and lots of others that
    are inherited from object by default. This works too and is simple.
    I'll deal with them when they become mandatory.
    """

    def __init__(self, f, args, kwargs):
        self._override = True
        self._isset = False
        self._value = None
        self._func = f
        self._args = args
        self._kwargs = kwargs
        self._override = False

    def _checkset(self):
        if not self._isset:
            self._override = True
            self._value = self._func(*self._args, **self._kwargs)
            self._isset = True
            self._checkset = lambda: True
            self._override = False

    def __getattr__(self, name):
        if self.__dict__["_override"]:
            return self.__dict__[name]
        self._checkset()
        return self._value.__getattribute__(name)

    def __setattr__(self, name, val):
        if name == "_override" or self._override:
            self.__dict__[name] = val
            return
        self._checkset()
        setattr(self._value, name, val)
        return


def lazy(f):
    """Lazy evaluation decorator"""

    def newf(*args, **kwargs):
        return _LazyWrapper(f, args, kwargs)

    return newf
