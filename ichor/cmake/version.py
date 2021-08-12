from ichor.common.types import Version
from ichor.cmake.check import run_cmake_version, cmake_present


class CMakeNotFound(Exception):
    pass


def cmake_current_version() -> Version:
    if not cmake_present():
        raise CMakeNotFound()
    output, _ = run_cmake_version()
    for line in output.split("\n"):
        if "cmake version" in line:
            return Version(line.split()[-1])
    raise CMakeNotFound()

