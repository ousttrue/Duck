import pathlib
import os
from typing import Optional
import vswhere


def find_cmake() -> Optional[pathlib.Path]:
    # search in PATH
    for p in os.getenv('PATH').split(';'):
        cmake = pathlib.Path(p) / 'cmake.exe'
        if cmake.exists():
            return cmake

    # default path
    cmake = pathlib.Path("C:/Program Files/CMake/bin/cmake.exe")
    if cmake.exists():
        return cmake

    # visual studio
    path = vswhere.get_latest_path()
    if path:
        vspath = pathlib.Path(path)
        cmake =  vspath / 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
        if cmake.exists():
            # add path to MSBuild
            msbuild_path = vspath / 'MSBuild\\Current\\Bin'
            os.environ['PATH'] = f'{msbuild_path};{os.environ["PATH"]}'

            return cmake

    return None

