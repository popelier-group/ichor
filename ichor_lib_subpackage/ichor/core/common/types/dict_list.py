class DictList(dict):
    """
    Wrapper around the common pattern of a dictionary of lists
    Allows for items of lists to be appended without checking the key
    exists first
    x = {}
    if k not in x.keys():
        x[k] = []
    x[k] += [v]

    Replaced by
    x = DictList()
    x[k] += [v]
    """

    def __init__(self, list_type=list):
        self.list_type = list_type

    def __getitem__(self, key):
        if key not in self.keys():
            self.__dict__[key] = self.list_type()
        return self.__dict__[key]
