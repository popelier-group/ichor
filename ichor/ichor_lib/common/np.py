from typing import Any, Dict, List

import numpy as np

from ichor.ichor_lib.itypes import Scalar


def dict_of_list_to_dict_of_array(
    dict_of_list: Dict[Any, List[Scalar]]
) -> Dict[Any, np.ndarray]:
    """
    Converst a dictionary of list of scalars to a dictionary of numpy arrays
    :param dict_of_list: dictionary mapping a key to a list of scalars (int or float)
    :return: dictionary mapping original keys to a numpy array converted from dict_of_list
    """
    return {key: np.array(value) for key, value in dict_of_list.items()}


def batched_array(a: np.ndarray, batch_size: int) -> np.ndarray:
    """
    :param a:           list
    :param batch_size:  size of each group
    :return:            Yields successive group-sized lists from l.
    """
    for i in range(0, len(a), batch_size):
        yield a[i : i + batch_size]
