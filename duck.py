import sys
import subprocess
import pathlib
import argparse
from typing import MutableMapping, Any
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


def do_entry(duck_toml: MutableMapping[str, Any],
             key: str,
             verbose=False,
             level=0) -> None:
    indent = '  ' * level

    # if exists ?
    entry = duck_toml.get(key)
    if not entry:
        raise KeyError(f'{key}: {duck_toml}')

    # depends
    depends = entry.get('depends')
    if depends:
        for d in depends:
            do_entry(duck_toml, d, verbose, level + 1)

    # do
    if verbose:
        print(f'{indent}[{key}]')
        print(f'{indent}{entry}')
    subprocess.run(entry['command'])


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

    duck_toml = toml.load(duck_file)

    verbose = args.verbose
    if '@verbose' in duck_toml:
        verbose = duck_toml['@verbose']
    if verbose:
        print(duck_toml)
        print()

    starts = args.starts
    if not starts:
        if len(duck_toml) == 1:
            starts = duck_toml.keys()
        elif '@default' in duck_toml:
            starts = [duck_toml['@default']]
        else:
            parser.print_help()
            sys.exit()

    for key in starts:
        do_entry(duck_toml, key, verbose)


if __name__ == '__main__':
    main()
