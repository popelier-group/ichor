from typing import Any, Dict, List
import inspect


def object_getattribute(obj: object, attr: str):
    return object.__getattribute__(obj, attr)


def object_hasattr(obj: object, attr: str) -> bool:
    try:
        object_getattribute(obj, attr)
        return True
    except AttributeError:
        return False


def object_getdict(obj: object) -> Dict[str, Any]:
    return object_getattribute(obj, "__dict__")


def object_setattr(obj: object, attr: str, value: Any):
    object.__setattr__(obj, attr, value)

def object_get_properties(obj: object) -> List[str]:
    return [p for p in dir(obj) if isinstance(getattr(obj.__class__, p), property)]

def object_get_properties_and_values(obj: object) -> Dict[str, Any]:
    return {prop: object_getattribute(obj, prop) for prop in object_get_properties(obj)}
