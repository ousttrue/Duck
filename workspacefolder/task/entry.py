import subprocess
import sys
import pathlib
from typing import Optional


def find_windows_cmake() -> Optional[pathlib.Path]:
    cmake = pathlib.Path("C:/Program Files/CMake/bin/cmake.exe")
    if cmake.exists():
        return cmake

    return None


class Entry:
    def __init__(self, system, t) -> None:
        self.system = system
        self.name = t['name'] # required
        self.command = t.get('command')
        self.depends = t.get('depends', [])
        self.cwd = t.get('cwd')
        self.encoding = t.get('encoding')
        self.parent = None

    def __str__(self):
        return f'<{self.name}>'

    def prepare_command(self) -> None:
        if self.command[0] == '::cmake::':
            if self.system == 'windows':
                cmake = find_windows_cmake()
                if cmake:
                    self.command[0] = str(cmake)
                    return

            self.command[0] = 'cmake'

    def do_entry(self, basepath: pathlib.Path, level=0) -> None:
        # indent = '  ' * level

        # depends
        if self.depends:
            for d in self.depends:
                d.do_entry(basepath, level + 1)

        # do
        print(f'[{self.name}]')
        if self.command:
            path = basepath
            if self.cwd:
                # relative from Duck.toml file
                path = basepath / self.cwd
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
            print(f'cwd: {path}')

            self.prepare_command()

            try:
                print(f'{self.command}')
                subprocess.run(self.command,
                        cwd=path,
                        encoding=self.encoding,
                        universal_newlines=True)
                print()
            except FileNotFoundError as e:
                print(f'{self.command[0]}: {e}')
                sys.exit(1)

