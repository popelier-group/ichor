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

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            try:
                return getattr(self.data, item)
            except AttributeError:
                for var, inst in self.__dict__.items():
                    if isinstance(inst, dict):
                        try:
                            if item in inst.keys():
                                return inst[item]
                        except AttributeError:
                            pass
            raise AttributeError("tmp error")