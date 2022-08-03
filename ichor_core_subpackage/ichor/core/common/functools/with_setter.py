class WithSetter:
    def __init__(self, func, callback):
        self._func = func
        self._callback = callback
        
    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
        
    def __get__(self, obj, objtype=None):
        if objtype is type(obj):
            return lambda *args, **kwargs: self(obj, *args, **kwargs)
        else:
            return lambda *args, **kwargs: self(*args, **kwargs)
    
    def __set__(self, obj, value):
        if isinstance(self._callback, str):
            self._callback = getattr(obj, self._callback)
        self._callback(value)


def with_setter(callback):
    def wrapper(func):
        return WithSetter(func, callback)
    return wrapper
