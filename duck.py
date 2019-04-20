import sys
import subprocess
import platform
import pathlib
import argparse
from typing import List, Any, Optional
import toml

VERSION = [0, 1]


def find_windows_cmake() -> Optional[pathlib.Path]:
    cmake = pathlib.Path("C:/Program Files/CMake/bin/cmake.exe")
    if cmake.exists():
        return cmake

    return None


class Duck:
    def __init__(self, path: pathlib.Path, verbose: bool, system: str) -> None:
        self.path = path
        self.toml = toml.load(path)
        self.verbose = False
        if '@verbose' in self.toml:
            self.verbose = self.toml['@verbose']
        if verbose:
            self.verbose = True
        if self.verbose:
            print(self.toml)
            print()
        self.system = system

    def get_command(self, entry: Any) -> Optional[List[str]]:
        command = entry.get('command')
        if not command:
            return None
        if isinstance(command, dict):
            command = command[self.system]
        return command

    def prepare_command(self, command: List[str]) -> None:
        if command[0] == '::cmake::':
            if self.system == 'windows':
                cmake = find_windows_cmake()
                if cmake:
                    command[0] = str(cmake)
                    return

            command[0] = 'cmake'

    def start(self, starts: List[str]) -> None:
        if not starts:
            if len(self.toml) == 1:
                starts = [k for k in self.toml.keys() if not k.startswith('@')]
            else:
                raise RuntimeError('no starts')

        if self.verbose:
            print(starts)

        for key in starts:
            self.do_entry(key)

    def do_entry(self, key: str, level=0) -> None:
        indent = '  ' * level
        if self.verbose:
            print(f'{indent}[{key}]')

        # if exists ?
        entry = self.toml.get(key)
        if not entry:
            raise KeyError(f'{key} not in {self.toml.keys()}')

        # depends
        depends = entry.get('depends')
        if depends:
            for d in depends:
                self.do_entry(d, level + 1)

        # do
        if self.verbose:
            print(f'{indent}{entry}')

        cwd = entry.get('cwd')
        command = self.get_command(entry)
        if command:
            path = self.path.parent
            if cwd:
                # relative from Duck.toml file
                path = path / cwd
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
            if self.verbose:
                print(f'{indent}{path}')

            self.prepare_command(command)

            encoding = entry.get('encoding')

            try:
                subprocess.run(command,
                               cwd=path,
                               encoding=encoding,
                               universal_newlines=True)
            except FileNotFoundError as e:
                print(f'{command[0]}: {e}')
                sys.exit(1)


def find_toml(current: pathlib.Path, verbose: bool) -> Optional[pathlib.Path]:

    while True:
        if verbose:
            print(current)
        duck_file = current / 'Duck.toml'
        if duck_file.exists():
            return duck_file

        if current == current.parent:
            print('Duck.toml not found')
            return None
        current = current.parent


def main():
    parser = argparse.ArgumentParser(
        description='a tool like make using TOML.')

    parser.add_argument('starts', type=str, nargs='*', help='start entries')

    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()
    if args.verbose:
        print(args)

    # find Duck.toml
    here = pathlib.Path('.').resolve()
    duck_file = find_toml(here, args.verbose)
    if not duck_file:
        return

    duck = Duck(duck_file, args.verbose, platform.system().lower())
    duck.start(args.starts)


if __name__ == '__main__':
    main()
