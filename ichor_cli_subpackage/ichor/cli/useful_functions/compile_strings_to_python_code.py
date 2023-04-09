from typing import List


def compile_strings_to_python_code(strings_list: List[str]) -> str:
    """Takes in a list of strings and concats them with a ; character
    Then these strings can be executed with python -c

    :param strings_list: _description_
    :type strings_list: List[str]
    :return: _description_
    :rtype: str
    """

    return ";".join(strings_list)
