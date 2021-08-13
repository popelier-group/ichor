from pathlib import Path
from ichor.common.types import Version
from ichor.cmake.version import cmake_current_version
from ichor.cmake.parser import Comment, Command, Arg, BlankLine, parse_cmake_lists
from ichor.common.functools import cached_property


class CMakeLists(list):
    """Top node of the syntax tree for a CMakeLists file."""
    def __init__(self, path: Path):
        '''
            Parses a string s in CMakeLists format whose
            contents are assumed to have come from the
            file at the given path.
            '''
        list.__init__(self)

        nums_items = parse_cmake_lists(path)
        [self.append(item) for _, item in nums_items]

    @cached_property
    def minimum_cmake_version(self):
        for line in self:
            if isinstance(line, Command) and line.name == "cmake_minimum_required":
                return Version(line.body[1].contents)
        return Version("2.0.0")

    def strip_blanks(self):
        self = [x for x in self if not isinstance(x, BlankLine)]

    @property
    def required_cmake_present(self) -> bool:
        return self.minimum_cmake_version < cmake_current_version()

    def ensure_required_cmake(self):
        if not self.required_cmake_present:
            update_cmake()
