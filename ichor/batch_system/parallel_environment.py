from ichor.common.types import RangeDict
from ichor.globals import Machine


class ParallelEnvironment(RangeDict):
    def __getitem__(self, item: int) -> str:
        try:
            return super().__getitem__(item)
        except KeyError:
            if item == 1:
                return ""
            raise KeyError(f"'ParallelEnvironment' for {item} cores not found")


class ParallelEnvironments(dict):
    def __getitem__(self, item: Machine) -> ParallelEnvironment:
        if item not in self.keys():
            self[item] = ParallelEnvironment()
        return super().__getitem__(item)
