import sys
import subprocess
import pathlib
import argparse
from typing import Dict, Any
import toml

VERSION = [0, 1]


def find_toml(current: pathlib.Path) -> pathlib.Path:
    while True:
        if not current.parent:
            raise RuntimeWarning('Duck.toml not found')

        duck_file = current / 'Duck.toml'
        if duck_file.exists():
            return duck_file

        current = current.parent


def do_entry(entry: Dict[str, Any]) -> None:
    subprocess.run(entry['command'])


def main():
    parser = argparse.ArgumentParser(
        description='a tool like make using TOML.')

    parser.add_argument('entry',
                        type=str,
                        nargs='*',
                        help='entry point of task')

    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()
    if args.verbose:
        print(args)

    # find Duck.toml
    here = pathlib.Path('.').resolve()
    duck_file = find_toml(here)

    duck_toml = toml.load(duck_file)
    if args.verbose:
        print(duck_toml)

    entry_points = args.entry
    if not entry_points:
        if len(duck_toml) == 1:
            entry_points = duck_toml.keys()
        elif 'default' in duck_toml:
            entry_points = [duck_toml['default']]

    for key in entry_points:
        entry = duck_toml.get(key)
        if not entry:
            raise KeyError(f'{key}: {duck_toml}')

        do_entry(entry)


if __name__ == '__main__':
    main()
