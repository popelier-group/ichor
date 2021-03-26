from ichor.common.types import ClassDict


class PropertyNotFound(Exception):
    pass


class GeometryData:
    def __init__(self):
        self.data = ClassDict()

    def get_property(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise PropertyNotFound(f"Property {item} not found")

    def __getitem__(self, item):
        try:
            return self.data[item]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__}' object has no attribute '{item}'"
            )

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            try:
                for var, inst in self.__dict__.items():
                    if isinstance(inst, (dict, ClassDict)):
                        if item in inst.keys():
                            return inst[item]
                raise AttributeError(
                    f"'{self.__class__}' object has no attribute '{item}'"
                )
            except KeyError:
                raise AttributeError(
                    f"'{self.__class__}' object has no attribute '{item}'"
                )
