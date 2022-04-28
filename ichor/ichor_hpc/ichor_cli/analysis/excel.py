import string


def col2num(col: str) -> int:
    """
    Returns the column number from the column name
    e.g.
    ```
    >>> col2num('A')
    1
    >>> col2num('Z')
    26
    >>> col2num('AB')
    28
    ```

    :param col: column name as string
    :return: column number
    """
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
    return num


def col2idx(col: str) -> int:
    """
    Returns the column number as a 0-index from the column name
    e.g.
    ```
    >>> col2idx('A')
    0
    >>> col2idx('Z')
    25
    >>> col2idx('AB')
    27
    ```

    :param col: column name as string
    :return: column number as 0-index
    """
    return col2num(col) - 1


def num2col(n: int) -> str:
    """
    Returns the name of the column given the column number
    e.g.
    ```
    >>> num2col(1)
    'A'
    >>> num2col(26)
    'Z'
    >>> num2col(28)
    'AB'
    ```
    :param n: column number
    :return: column name as string
    """
    name = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(r + ord("A")) + name
    return name


def idx2col(n: int) -> str:
    """
    Returns the name of the column given the column index
    e.g.
    ```
    >>> num2col(0)
    'A'
    >>> num2col(25)
    'Z'
    >>> num2col(27)
    'AB'
    ```
    :param n: column index
    :return: column name as string
    """
    return num2col(n + 1)
