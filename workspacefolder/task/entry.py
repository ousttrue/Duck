import subprocess
import sys
import pathlib
from typing import Optional
from . import windows_tool_search


class Entry:
    def __init__(self, system, t) -> None:
        self.system = system
        self.name = t['name']  # required
        self.command = t.get('command')
        self.depends = t.get('depends', [])
        self.cwd = t.get('cwd')
        self.encoding = t.get('encoding')
        self.parent = None
        self.retcode = t.get('retcode')
        self.if_not_exists = t.get('if_not_exists')

    def __str__(self):
        return f'<{self.name}>'

    def prepare_command(self) -> None:
        if self.command[0] == 'cmake':
            if self.system == 'windows':
                cmake = windows_tool_search.find_cmake()
                if cmake:
                    self.command[0] = str(cmake)
                    return

            self.command[0] = 'cmake'

    def do_entry(self, basepath: pathlib.Path, level=0) -> None:
        # indent = '  ' * level

        # depends
        if self.depends:
            for depend in self.depends:
                depend.do_entry(basepath, level + 1)

        # do
        if self.if_not_exists:
            if (basepath / self.if_not_exists).exists():
                return

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

            print('# ' + ' '.join(self.command))
            p = None
            try:
                p = subprocess.Popen(self.command,
                               cwd=path,
                               encoding=self.encoding,
                               universal_newlines=True)
                ret = p.wait()
                print(f'ret = {ret}')
                if not self.retcode:
                    if ret!=0:
                        sys.exit(ret)
                print()

            except FileNotFoundError as error:
                print(f'{error}: {self.command[0]}')
                sys.exit(1)

            finally:
                if p and p.returncode is None:
                    print('kill')
                    p.kill()

