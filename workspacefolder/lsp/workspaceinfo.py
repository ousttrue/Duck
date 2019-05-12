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

# python {{{
def get_python_root(path: pathlib.Path) -> pathlib.Path:
    current = path.parent
    while True:
        if any(f.name == 'setup.py' for f in current.iterdir()):
            return current

        if current == current.parent:
            break
        current = current.parent
    return path


class PylsWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        path = get_python_root(path.parent)
        super().__init__(path, 'python', 'pyls')

    def launch(self) -> languageserver.LanguageServer:
        return languageserver.LanguageServer(self.path, self.cmd, *self.args)
# }}}

def get_workspaceinfo(path: pathlib.Path) -> Optional[WorkspaceInfo]:
    if path.suffix == '.py':
        return PylsWorkspaceInfo(path)

    logger.warn('not implemented: %s', path)
    return None
