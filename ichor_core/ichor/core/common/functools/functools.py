import threading
from functools import wraps
from time import time

from ichor.core.common.types.itypes import F, Scalar, T

try:
    import asyncio
except (ImportError, SyntaxError):
    asyncio = None
from typing import Any, Sequence


def buildermethod(func: F) -> F:
    """
    Executes a function on an instance of a class and returns the modified instance.
    This allows for scenarios where we can initialize a class and call a method
    (which does not return anything but it does modify the instance) in the same line.

    :param func: The function to be executed

    .. note::

        Without builder decorator:
            t = Test().add() Since the add() method does not return anything, t is `None`

        With @builder decorator:
            t = Test().add() Since the add() method does not return anything, t is an instance of test

        Without builder method:
        t = Test()
        t.add()
    """

    # makes sure that func.__name__ returns the name of the
    # function instead of wrapper if the decorator has been applied to func
    @wraps(func)
    def wrapper(self: T, *args, **kwargs) -> T:
        func(self, *args, **kwargs)
        return self

    return wrapper


# cached property


class cached_property(object):
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """  # noqa

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self

        if asyncio and asyncio.iscoroutinefunction(self.func):
            return self._wrap_in_coroutine(obj)

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value

    def _wrap_in_coroutine(self, obj):
        @wraps(obj)
        @asyncio.coroutine
        def wrapper():
            future = asyncio.ensure_future(self.func(obj))
            obj.__dict__[self.func.__name__] = future
            return future

        return wrapper()


class threaded_cached_property(object):
    """
    A cached_property version for use in environments where multiple threads
    might concurrently try to access the property.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func
        self.lock = threading.RLock()

    def __get__(self, obj, cls):
        if obj is None:
            return self

        obj_dict = obj.__dict__
        name = self.func.__name__
        with self.lock:
            try:
                # check if the value was computed before the lock was acquired
                return obj_dict[name]

            except KeyError:
                # if not, do the calculation and release the lock
                return obj_dict.setdefault(name, self.func(obj))


class cached_property_with_ttl(object):
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Setting the ttl to a number expresses how long
    the property will last before being timed out.
    """

    def __init__(self, ttl=None):
        if callable(ttl):
            func = ttl
            ttl = None
        else:
            func = None
        self.ttl = ttl
        self._prepare_func(func)

    def __call__(self, func):
        self._prepare_func(func)
        return self

    def __get__(self, obj, cls):
        if obj is None:
            return self

        now = time()
        obj_dict = obj.__dict__
        name = self.__name__
        try:
            value, last_updated = obj_dict[name]
        except KeyError:
            pass
        else:
            ttl_expired = self.ttl and self.ttl < now - last_updated
            if not ttl_expired:
                return value

        value = self.func(obj)
        obj_dict[name] = (value, now)
        return value

    def __delete__(self, obj):
        obj.__dict__.pop(self.__name__, None)

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = (value, time())

    def _prepare_func(self, func):
        self.func = func
        if func:
            self.__doc__ = func.__doc__
            self.__name__ = func.__name__
            self.__module__ = func.__module__


class cached_property_with_ntimes(object):
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Setting the ntimes to a number expresses how many
    times the property can be called before being recalculated
    """

    def __init__(self, ntimes=None):
        if callable(ntimes):
            func = ntimes
            ntimes = None
        else:
            func = None
        self.ntimes = ntimes
        self._prepare_func(func)

    def __call__(self, func):
        self._prepare_func(func)
        return self

    def __get__(self, obj, cls):
        if obj is None:
            return self

        obj_dict = obj.__dict__
        name = self.__name__
        try:
            value, ntimes_called = obj_dict[name]
        except KeyError:
            pass
        else:
            ntimes_expired = self.ntimes and self.ntimes <= ntimes_called
            if not ntimes_expired:
                obj_dict[name] = (value, ntimes_called + 1)
                return value

        value = self.func(obj)
        obj_dict[name] = (value, 1)
        return value

    def __delete__(self, obj):
        obj.__dict__.pop(self.__name__, None)

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = (value, 1)

    def _prepare_func(self, func):
        self.func = func
        if func:
            self.__doc__ = func.__doc__
            self.__name__ = func.__name__
            self.__module__ = func.__module__


# Aliases to make cached_property_with_ttl easier to use
cached_property_ttl = cached_property_with_ttl
timed_cached_property = cached_property_with_ttl


class threaded_cached_property_with_ttl(cached_property_with_ttl):
    """
    A cached_property version for use in environments where multiple threads
    might concurrently try to access the property.
    """

    def __init__(self, ttl=None):
        super(threaded_cached_property_with_ttl, self).__init__(ttl)
        self.lock = threading.RLock()

    def __get__(self, obj, cls):
        with self.lock:
            return super(threaded_cached_property_with_ttl, self).__get__(obj, cls)


# Alias to make threaded_cached_property_with_ttl easier to use
threaded_cached_property_ttl = threaded_cached_property_with_ttl
timed_threaded_cached_property = threaded_cached_property_with_ttl
ntimes_cached_property = cached_property_with_ntimes


# class property


class ClassPropertyDescriptor:
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func: F) -> ClassPropertyDescriptor:
    """A decorator which makes it possible to make class properties,
    where the class can call a class method without the parenthesis at the end.
    This is useful to have as class variables are static and cannot be changed.
    Class properties allow us to change these values on the fly."""
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassPropertyDescriptor(func)


# run function


def run_function(order: Scalar) -> F:
    """Used to decorate a method so that `get_functions_to_run` can find and return the methods in
    the order specified by the order parameter"""

    def decorator(func: F) -> F:
        func._order = order

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_functions_to_run(obj: Any) -> Sequence[F]:
    """Finds all methods of `obj` with the `order` attribute then returns the sequence of methods
    in the order defined"""
    return sorted(
        [
            getattr(obj, field)
            for field in dir(obj)
            if hasattr(getattr(obj, field), "_order")
        ],
        key=(lambda field: field._order),
    )


# run once


def run_once(func: F) -> F:
    """Decorator which only runs the function the first
    time it is called and stores the result. If the function is ran another time, the stored result is
    returned."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if hasattr(func, "has_run"):
            return func.return_value
        func.return_value = func(*args, **kwargs)
        func.has_run = True
        return func.return_value

    return wrapper
