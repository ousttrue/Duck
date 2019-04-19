import sys
import subprocess
import pathlib
import argparse
from typing import MutableMapping, Any, List
import toml

VERSION = [0, 1]


class Duck:
    def __init__(self, path: pathlib.Path, verbose: bool) -> None:
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

    def start(self, starts: List[str]) -> None:
        if not starts:
            if len(self.toml) == 1:
                starts = self.toml.keys()
            elif '@default' in self.toml:
                starts = [self.toml['@default']]
            else:
                raise RuntimeError('no starts')
        for key in starts:
            self.do_entry(key)

    def do_entry(self, key: str, level=0) -> None:
        indent = '  ' * level

        # if exists ?
        entry = self.toml.get(key)
        if not entry:
            raise KeyError(f'{key}: {self.toml}')

        # depends
        depends = entry.get('depends')
        if depends:
            for d in depends:
                self.do_entry(d, level + 1)

        # do
        if self.verbose:
            print(f'{indent}[{key}]')
            print(f'{indent}{entry}')

        cwd = entry.get('cwd')
        command = entry.get('command')
        if command:
            path = self.path.parent
            if cwd:
                # relative from Duck.toml file
                path = path / cwd
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
            if self.verbose:
                print(f'{indent}{path}')
            subprocess.run(entry['command'], cwd=path)


def find_toml(current: pathlib.Path) -> pathlib.Path:
    while True:
        if not current.parent:
            raise RuntimeWarning('Duck.toml not found')

        duck_file = current / 'Duck.toml'
        if duck_file.exists():
            return duck_file

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
    duck_file = find_toml(here)

    duck = Duck(duck_file, args.verbose)
    duck.start(args.starts)


if __name__ == '__main__':
    main()
