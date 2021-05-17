from typing import Dict, Optional
import numpy as np


class ModelResult(dict):
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

    def __add__(self, other: 'ModelResult'):
        if isinstance(other, ModelResult):
            return self._add_result(other)
        else:
            return self._add_value(other)

    def __sub__(self, other: 'ModelResult'):
        if isinstance(other, ModelResult):
            return self._sub_result(other)
        else:
            return self._sub_value(other)

    def __mul__(self, other: 'ModelResult'):
        if isinstance(other, ModelResult):
            return self._mul_result(other)
        else:
            return self._mul_value(other)

    def __div__(self, other: 'ModelResult'):
        if isinstance(other, ModelResult):
            return self._div_result(other)
        else:
            return self._div_value(other)

    def __radd__(self, other: float):
        if isinstance(other, ModelResult):
            return self._add_result(other)
        else:
            return self._add_value(other)

    def __rsub__(self, other: float):
        if isinstance(other, ModelResult):
            return self._rsub_result(other)
        else:
            return self._rsub_value(other)

    def __rmul__(self, other: float):
        if isinstance(other, ModelResult):
            return self._mul_result(other)
        else:
            return self._mul_value(other)

    def __rdiv__(self, other: float):
        if isinstance(other, ModelResult):
            return self._rdiv_result(other)
        else:
            return self._rdiv_value(other)

    def __eq__(self, other):
        a = []
        if not isinstance(other, dict):
            return False

        for key, val in self.items():
            if isinstance(val, np.ndarray) and isinstance(other[key], np.ndarray):
                a += [(val == other[key]).all()]
            elif key in other.keys():
                a += [val == other[key]]
            else:
                return False
        return all(a)

    def _reduce(self):
        result = ModelResult()
        for key, val in self.items():
            result[key] = val if not isinstance(val, ModelResult) else sum(val.values())
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


class ModelsResult(ModelResult):
    def __init__(self, result: Optional[Dict[str, Dict[str, np.ndarray]]] = None):
        ModelResult.__init__(self)
        if result is not None:
            for key, val in result.items():
                self[key] = ModelResult(val)
