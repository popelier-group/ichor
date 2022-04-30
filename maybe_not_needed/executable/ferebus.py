from pathlib import Path

from ichor.cmake import CMakeLists, update_cmake
from ichor.ichor_lib.common.io import mkdir, pushd
from ichor.ichor_lib.common.os import run_cmd
from ichor.executable.executable import Executable
from ichor.modules import FerebusModules, load_module


class Ferebus(Executable):
    def __init__(self):
        Executable.__init__(
            self, git_repository="https://github.com/popelier-group/FEREBUS"
        )

    @property
    def exepath(self) -> Path:
        return self.path / "build" / "ferebus"

    def build(self):
        load_module(FerebusModules)
        with pushd(self.path):
            cmake = CMakeLists(self.path / "CMakeLists.txt")
            if not cmake.required_cmake_present:
                update_cmake(cmake.minimum_cmake_version)
            mkdir("build")
            with pushd("build"):
                run_cmd(["cmake", "..", "-DCMAKE_BUILD_TYPE=RELEASE"])
                run_cmd(["make"])
