import sys
import subprocess
import platform
import pathlib
import argparse
from typing import List, Any, Optional, NamedTuple
import toml
import logging
logger = logging.getLogger(__name__)


def find_windows_cmake() -> Optional[pathlib.Path]:
    cmake = pathlib.Path("C:/Program Files/CMake/bin/cmake.exe")
    if cmake.exists():
        return cmake

    return None


class Task:
    def __init__(self, t) -> None:
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
                    command[0] = str(cmake)
                    return

            self.command[0] = 'cmake'

    def do_entry(self, basepath: pathlib.Path, level=0) -> None:
        indent = '  ' * level

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
                print(f'{command[0]}: {e}')
                sys.exit(1)


class Duck:
    def __init__(self, path: pathlib.Path, verbose: bool, system: str) -> None:
        self.path = path
        self.toml = toml.load(path)
        self.verbose = verbose
        if self.verbose:
            logger.debug(self.toml)
        self.system = system

        def get_tasks(toml):
            if 'tasks' not in toml:
                return []
            return toml['tasks']
        self.tasks = {t['name']: Task(t) for t in get_tasks(self.toml)}
        for k, v in self.tasks.items():
            depends = [self.tasks[x] for x in v.depends]
            v.depends = depends

        self.root = []
        for k, v in self.tasks.items():
            if not any((v in _v.depends) for _k, _v in self.tasks.items()):
                self.root.append(v)

    def start(self, starts: List[str]) -> None:
        if self.verbose:
            print(starts)

        for key in starts:
            self.tasks[key].do_entry(self.path.parent)


def find_toml(current: pathlib.Path, verbose: bool) -> Optional[pathlib.Path]:

    while True:
        if verbose:
            print(current)
        duck_file = current / 'Workspace.toml'
        if duck_file.exists():
            return duck_file

        if current == current.parent:
            print('Workspace.toml not found')
            return None
        current = current.parent


def execute(parsed) -> bool:
    # find Workspace.toml
    here = pathlib.Path('.').resolve()
    duck_file = find_toml(here, parsed.debug)
    if not duck_file:
        print('[Workspace.toml]')
        print('not found')
        print()
        return False

    duck = Duck(duck_file, parsed.debug, platform.system().lower())

    if parsed.args:
        duck.start(parsed.args)
    else:
        print('[Workspace.toml]')
        print(duck_file.resolve())
        print()
        if duck.tasks:
            print('[task entries]')
            def traverse(task, level = 0):
                print(f'{"    " * level}{task}')
                if task.depends:
                    for d in task.depends:
                        traverse(d, level+1)

            for task in duck.root:
                traverse(task)
    return True
