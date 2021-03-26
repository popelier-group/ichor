class ClassDict(dict):
    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value
