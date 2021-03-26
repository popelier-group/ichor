class Modules(dict):
    def __getitem__(self, item) -> list:
        if item not in self.keys():
            return []
        return super().__getitem__(item)
