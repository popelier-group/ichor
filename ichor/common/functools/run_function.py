from functools import wraps


def run_function(order):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func.order = order
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_functions_to_run(obj):
    return sorted(
        [
            getattr(obj, field)
            for field in dir(obj)
            if hasattr(getattr(obj, field), "order")
        ],
        key=(lambda field: field.order),
    )
