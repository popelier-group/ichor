from typing import Tuple


class RangeDict(dict):
    """A dictionary which overrides the __getitem__ and __setitem__ methods.
    This class is used to get the
    correct batch script keywords for core counts.

    .. note::
        Here is an example of how the RangeDict class works. d[2] asks for 2 cores,
        since 2 is between 1 and 4, this will return "a"
        d = RangeDict()
        d['a'] = (1, 4)
        d['b'] = (5, 9)
        d[2]
        >> 'a'
    """

    def __getitem__(self, item: int) -> str:
        """Overrides __getitem__ method to return the key for which `item`
        is between the tuple stored as the value for that key.

        :param item: An integer which represents the number of cores to use for the job.
        """
        # iterate over key and value pairs in dictionary (value pairs is a tuple with lower and upper bound)
        for key, (minval, maxval) in self.items():
            # if the item fits in the range given by the tuple then return the key
            if minval <= item <= maxval:
                # the key corresponds to the keyword that is
                # used to specify the number of cores (depending on machine)
                return key
        raise KeyError(f"'{item}' not found in '{self.__class__.__name__}'")

    def __setitem__(self, key: str, value: Tuple[int, int]):
        """Adds a key:value pair to the dictionary.

        :param key: A string that represents the keyword used when selecting the number of CPU cores for the job.
        :param value: A tuple containing two int elements:
            A lower and upper boundary for the cores the job can utilize.
        """
        if not isinstance(key, str):
            raise TypeError(
                f"Key for '{self.__class__.__name__}' must be of type 'str'"
            )
        if not len(value) == 2:
            raise TypeError(
                f"Value for '{self.__class__.__name__}' must be a sequence of length 2"
            )
        super().__setitem__(key, (value[0], value[1]))
