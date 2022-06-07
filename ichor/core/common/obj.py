from typing import Any, Dict


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
