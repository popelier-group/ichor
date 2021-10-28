from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

import numpy as np

from ichor.itypes import Scalar

# TODO: we should aways use numpy, python lists are way slower and we only need to store numerical data anyway. No need in having lists as well
convert_to_numpy = True


def is_list_of_scalars(l):
    return all(isinstance(i, (int, np.int, float, np.float)) for i in l)


class ArithMixin(ABC):
    @abstractmethod
    def _add_value(self, other):
        pass

    @abstractmethod
    def _add_result(self, other):
        pass

    @abstractmethod
    def _sub_value(self, other):
        pass

    @abstractmethod
    def _sub_result(self, other):
        pass

    @abstractmethod
    def _rsub_value(self, other):
        pass

    @abstractmethod
    def _rsub_result(self, other):
        pass

    @abstractmethod
    def _mul_value(self, other):
        pass

    @abstractmethod
    def _mul_result(self, other):
        pass

    @abstractmethod
    def _div_value(self, other):
        pass

    @abstractmethod
    def _div_result(self, other):
        pass

    @abstractmethod
    def _rdiv_value(self, other):
        pass

    @abstractmethod
    def _rdiv_result(self, other):
        pass

    def __add__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._add_result(other)
        else:
            return self._add_value(other)

    def __sub__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._sub_result(other)
        else:
            return self._sub_value(other)

    def __mul__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._mul_result(other)
        else:
            return self._mul_value(other)

    def __div__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._div_result(other)
        else:
            return self._div_value(other)

    def __radd__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._add_result(other)
        else:
            return self._add_value(other)

    def __rsub__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._rsub_result(other)
        else:
            return self._rsub_value(other)

    def __rmul__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._mul_result(other)
        else:
            return self._mul_value(other)

    def __rdiv__(self, other: Union[Scalar, "ArithMixin"]):
        if isinstance(other, ArithMixin):
            return self._rdiv_result(other)
        else:
            return self._rdiv_value(other)

    @abstractmethod
    def _abs_result(self):
        pass

    def abs(self):
        return self._abs_result()


class ModelResult(dict, ArithMixin):

    def _add_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = val + other
        return result

    def _add_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = val + other[key]
        return result

    def _sub_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = val - other
        return result

    def _sub_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = val - other[key]
        return result

    def _rsub_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = other - val
        return result

    def _rsub_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = other[key] - val
        return result

    def _mul_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = val * other
        return result

    def _mul_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = val * other[key]
        return result

    def _div_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = val / other
        return result

    def _div_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = val / other[key]
        return result

    def _rdiv_value(self, other):
        result = ModelResult()
        for key, val in self.items():
            result[key] = other / val
        return result

    def _rdiv_result(self, other):
        result = ModelResult()
        for key, val in self.items():
            if key in other.keys():
                result[key] = other[key] / val
        return result

    def _abs_result(self):
        result = ModelResult()
        for key, val in self.items():
            if isinstance(val, ArithMixin):
                result[key] = val.abs()
            else:
                result[key] = np.abs(val)
        return result

    def len(self) -> int:
        lengths = []
        for val in self.values():
            if isinstance(val, ModelResult):
                lengths += [val.len()]
            else:
                lengths += [len(val)]
        return max(lengths)

    def __eq__(self, other):
        a = []
        if not isinstance(other, dict):
            return False

        for key, val in self.items():
            if isinstance(val, np.ndarray) and isinstance(
                other[key], np.ndarray
            ):
                a += [(val == other[key]).all()]
            elif key in other.keys():
                a += [val == other[key]]
            else:
                return False
        return all(a)

    def _reduce(self):
        result = ModelResult()
        for key, val in self.items():
            result[key] = (
                val if not isinstance(val, ModelResult) else sum(val.values())
            )
        return result

    def reduce(self, level=1):
        result = ModelResult(self)
        prev_result = ModelResult(result)
        while level != 0:
            result = result._reduce()
            if prev_result == result:
                result = sum(result.values())
                break
            prev_result = ModelResult(result)
            level -= 1
        return result

    def to_list(self):
        # TODO: we should aways use numpy, python lists are way slower and we only need to store numerical data anyway. No need in having lists as well
        global convert_to_numpy
        convert_to_numpy = False
        result = ModelResult()
        for key, val in self.items():
            if isinstance(val, ModelResult):
                result[key] = val.to_list()
            elif isinstance(val, np.ndarray):
                result[key] = list(val)
            else:
                result[key] = val
        convert_to_numpy = True
        return result

    def __getitem__(self, item):
        if not isinstance(item, str):
            result = ModelResult()
            for key, val in self.items():
                result[key] = val.__getitem__(item)
            return result
        return super().__getitem__(item)

    def __setitem__(self, key, value):
        if (
            isinstance(value, list)
            and is_list_of_scalars(value)
            and convert_to_numpy
        ):
            value = np.array(value)
        super().__setitem__(key, value)

    def array(self) -> np.ndarray:
        if len(self) == 1:
            values = next(iter(self.values()))
            if isinstance(values, np.ndarray):
                return values
            else:
                return values.array()
        else:
            raise ValueError(
                f"Can only return 'array' of '{self.__class__.__name__}' of length 1"
            )


class ModelsResult(ModelResult):
    """ A dictionary of dictionaries which has some extra methods defines which allows us to modify dictionary values easily.
    Typically the structure of this dictionary of dictionaries is: `{atom_name0: {property0: np.ndarray, property1: np.ndarray,...}, 
    atom_name1: {property0: np.ndarray, property1: np.ndarray,...}, ...}`. So for example it might look somethin like 
    `{"O1": {"q00": np.ndarray, "q10": np.ndarray,...}, "H2": {"q00": np.ndarray, "q10": np.ndarray,...}}`
    """

    def __init__(
        self, result: Optional[Dict[str, Dict[str, np.ndarray]]] = None
    ):
        ModelResult.__init__(self)
        if result is not None:
            for key, val in result.items():
                self[key] = ModelResult(val)

    def append(self, other):
        if isinstance(other, ModelsResult):
            for key, val in other.items():
                self[key] = val
        else:
            raise TypeError(
                f"Cannot append value of type '{type(other)}' to type '{self.__class__.__name__}"
            )

    @property
    def T(self):
        """ Transposes the dictionary, making the inner dictionary's keys the outer dictionary's keys and vice versa.
        
        For example, `{"O1": {"q00": np.ndarray, "q10": np.ndarray,...}, "H2": {"q00": np.ndarray, "q10": np.ndarray,...}}`
        will become `{"q00": {"O1": np.ndarray, "H2": np.ndarray,...}, "q10": {"O1": np.ndarray, "H2": np.ndarray,...}}`
        """
        result = ModelsResult()
        for key, val in self.items():
            for mkey, mval in val.items():
                if mkey not in result.keys():
                    result[mkey] = ModelResult()
                result[mkey][key] = mval
        return result

    # todo: if not used better to delete it
    def split(self):
        return SplitResult(self)

    # todo: if not used better to delete it
    def group(self):
        return self.T.split()

# todo: if this is not used better to delete it
class ListResult(list, ArithMixin):
    def __getitem__(self, item: int):
        if item >= len(self):
            for _ in range(len(self) - 1, item):
                self.append(ModelResult())
        return super().__getitem__(item)

    def _reduce(self):
        result = ListResult()
        for i, val in enumerate(self):
            result += [val._reduce()]
        if is_list_of_scalars(result):
            result = np.array(result)
        return result

    def reduce(self, level=1):
        result = self._reduce()
        if len(result) == 1:
            return result[0]
        return result

    def _add_value(self, other):
        result = ListResult()
        for val in self:
            result += [val + other]
        return result

    def _add_result(self, other):
        return self._add_value(other)

    def _sub_value(self, other):
        result = ListResult()
        for val in self:
            result += [val - other]
        return result

    def _sub_result(self, other):
        return self._sub_value(other)

    def _rsub_value(self, other):
        result = ListResult()
        for val in self:
            result += [other - val]
        return result

    def _rsub_result(self, other):
        return self._rsub_value(other)

    def _mul_value(self, other):
        result = ListResult()
        for val in self:
            result += [val * other]
        return result

    def _mul_result(self, other):
        return self._mul_value(other)

    def _div_value(self, other):
        result = ListResult()
        for val in self:
            result += [val / other]
        return result

    def _div_result(self, other):
        return self._div_value(other)

    def _rdiv_value(self, other):
        result = ListResult()
        for val in self:
            result += [other / val]
        return result

    def _rdiv_result(self, other):
        return self._rdiv_value(other)


# todo: if this is not used better to delete it
class SplitResult(ModelResult):
    def __init__(self, result: Optional[ModelsResult] = None):
        ModelResult.__init__(self)
        if result:
            if isinstance(result, ModelsResult):
                self.init(result)
            elif isinstance(result, SplitResult):
                self.init_from_split(result)
            else:
                raise TypeError(
                    f"Cannot init type 'SplitResult' from type '{type(result)}'"
                )

    def init(self, result: ModelsResult):
        for key, val in result.items():
            self[key] = ListResult()
            for mkey, mval in val.items():
                for i, v in enumerate(mval):
                    self[key][i][mkey] = v

    def init_from_split(self, result: "SplitResult"):
        for key, val in result.items():
            self[key] = val

    def _reduce(self):
        result = ListResult()
        for key, val in self.items():
            result += [val._reduce()]
        return result

    def reduce(self, level=1):
        result = self
        prev_result = result
        while level != 0:
            result = result._reduce()
            if prev_result == result:
                result = result.reduce()
                break
            prev_result = result
            level -= 1
        return result
