from abc import ABC
from typing import Any
from ichor_lib.files import File

class PropertyNotFound(Exception):
    pass

class GeometryData(dict):
    """ Used to be able to distinguish between a normal dictionary instance
    and a GeometryData instance. Otherwise, the same as a normal dictionary."""
    pass

class GeometryDataFile(File, ABC):
    """
    Class used to describe a file containing properties/data for a particular geometry

    Adds the method `get_property` which can be used to search for a property of a geometry
    Adds the ability to search for a property using dictionaries in the inherited class
    """

    def get_property(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise PropertyNotFound(f"Property {item} not found")

    def __getattr__(self, item: str) -> Any:
        """ Used to make values of GeometryData instances accessible as attributes.
        Looks into __dict__ of an instance to see if an instance of GeometryData exist.
        If an instance of GeometryData exists, it looks at the keys of that instance
        and the value is returned."""
        # loop over __dict__ (vars(self)) and find any attributes which are dictionaries.
        # if the dictionary keys contain the item of interest, then return the value associated with this dictionary key.
        # todo: implement method for combining multiple dictionaries with identical keys
        for instance in vars(self).values():
            if isinstance(instance, GeometryData) and item in instance.keys():
                return instance[item]

        raise AttributeError(
            f"{self.__class__} object has no attribute {item}."
        )


class AtomicDict(dict):
    def __getattr__(self, item):
        """
        If an attribute is requested that is not in INTs but is an attribute of INT, a dictionary
        of the attributes are returned. e.g.

        ```python
        >>> ints.iqa
        {'O1': 76.51, 'H2': 0.52, 'H3': 0.53}
        ```
        """
        try:
            return {atom: getattr(int_, item) for atom, int_ in self.items()}
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            )
