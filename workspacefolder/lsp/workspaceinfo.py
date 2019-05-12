import pathlib
import logging
from typing import List, Optional
from . import languageserver
logger = logging.getLogger(__name__)


class WorkspaceInfo:
    def __init__(self, path: pathlib.Path, language: str, cmd: str,
                 *args: List[str]) -> None:
        self.path = path
        self.language = language
        self.cmd = cmd
        self.args = args

    def launch(self) -> languageserver.LanguageServer:
        return languageserver.LanguageServer(self.language, self.path,
                                             self.cmd, *self.args)


def find_to_ancestors(path: pathlib.Path,
                      target: str) -> Optional[pathlib.Path]:
    current = path.parent
    while True:
        for f in current.iterdir():
            if f.name == target:
                return f
    return None


class PylsWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'python', 'pyls')


class DlsWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'd', 'dub', 'run', 'dls')

class ServeDWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'd', 'dub', 'run', '-a', 'x86_mscoff', 'serve-d')


def get_workspaceinfo(path: pathlib.Path) -> Optional[WorkspaceInfo]:
    if path.suffix == '.py':
        found = find_to_ancestors(path.parent, 'setup.py')
        return PylsWorkspaceInfo(found.parent if found else path.parent)
    elif path.suffix == '.d':
        found = find_to_ancestors(path.parent, 'dub.json')
        if found:
            # require dub.json
            return DlsWorkspaceInfo(found.parent)
            #return ServeDWorkspaceInfo(found.parent / 'source')

    #logger.warn('not implemented: %s', path)
    return None
