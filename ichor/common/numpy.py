from typing import Any, Dict, List

import numpy as np

from ichor.itypes import Scalar


def dict_of_list_to_dict_of_array(
    dict_of_list: Dict[Any, List[Scalar]]
) -> Dict[Any, np.ndarray]:
    """
    Converst a dictionary of list of scalars to a dictionary of numpy arrays
    :param dict_of_list: dictionary mapping a key to a list of scalars (int or float)
    :return: dictionary mapping original keys to a numpy array converted from dict_of_list
    """
    return {key: np.array(value) for key, value in dict_of_list.items()}
