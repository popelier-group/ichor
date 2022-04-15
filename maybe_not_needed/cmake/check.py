from typing import Tuple

from ichor.common.os import run_cmd


def run_cmake_version() -> Tuple[str, str]:
    return run_cmd(["cmake", "--version"])


def cmake_present() -> bool:
    _, error = run_cmake_version()
    return error == ""
