class ClassDict(dict):
    """ A helper class which allows access to items stored in self (which is a dictionary) as if they were attributes (by using dot notation) instead of
    indexing like a dictionary """
    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        """ All attributes are also stored in the dictionary so that the attribute and dictionary value are always synced """
        self[key] = value
