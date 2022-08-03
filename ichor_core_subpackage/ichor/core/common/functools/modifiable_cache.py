from functools import _lru_cache_wrapper, _CacheInfo
from collections import Hashable 

class NotSetType:
    def __str__(self):
        return "NotSet"

NotSet = NotSetType()


def get_first_arg(*args, **kwargs):
    if len(args) > 0:
        return args[0]
    
    if len(kwargs) > 0:
        return next(iter(kwargs.values()))
    
    return NotSet
    
from collections.abc import Hashable, Iterable

def is_hashable(item):
    hashable = isinstance(item, Hashable)
    if hashable and isinstance(item, Iterable) and not isinstance(item, str):
        return all(is_hashable(i) for i in item)
    return hashable


class modifiable_cache:
    def __init__(self, func):
        self._func = _lru_cache_wrapper(func, None, False, _CacheInfo)
        self._cache = {}
    
    def set_return_val(self, return_val):
        self._cache = return_val

    def __call__(self, *args, **kwargs):
        first_arg = get_first_arg(*args, **kwargs)
        if is_hashable(first_arg) and first_arg in self._cache.keys():
            return self._cache[first_arg]
        else:
            return self._func(*args, **kwargs)

    def __get__(self, obj, objtype=None):
        print(self._cache)
        if objtype is type(obj):
            return lambda *args, **kwargs: self(obj, *args, **kwargs)
        else:
            return lambda *args, **kwargs: self(*args, **kwargs)

    def __set__(self, obj, value):
        self._cache[obj] = value
