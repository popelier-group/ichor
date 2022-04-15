#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tarfile
from pathlib import Path

import requests

from ichor.common.io import recursive_move, remove
from ichor.common.sys import access_internet
from ichor.globals import GLOBALS, OS


def update_cmake(cmake_version):
    cmake_ext = ""
    if GLOBALS.OS is OS.Linux:
        cmake_ext = "linux-x86_64"
    elif GLOBALS.OS is OS.MacOS:
        cmake_ext = "macos-universal"
    elif GLOBALS.OS is OS.Windows:
        cmake_ext = "windows-x86_64"

    access_internet()

    targz = Path(f"cmake-{cmake_version}-{cmake_ext}.tar.gz")
    url = f"https://github.com/Kitware/CMake/releases/download/v{cmake_version}/{targz}"
    target_path = Path.home() / Path(f".local/scratch/{targz}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            f.write(response.raw.read())
    tar = tarfile.open(target_path, "r:gz")
    tar.extractall(path=target_path.parent)
    tar.close()

    for f in Path(target_path.parent / Path(targz.stem).stem).iterdir():
        recursive_move(f, Path.home() / ".local")

    # Cleanup Files
    remove(target_path)
    remove(Path(target_path.parent / Path(targz.stem).stem))

    os.environ["PATH"] = (
        str(Path.home() / Path(".local") / Path("bin"))
        + os.pathsep
        + os.environ["PATH"]
    )
