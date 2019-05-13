import pathlib
import glob
import logging
from typing import List, Optional
from . import languageserver
logger = logging.getLogger(__name__)
HERE = pathlib.Path(__file__).resolve().parent

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

        for f in current.glob(target):
            return f
        if current == current.parent:
            break
        current = current.parent
    return None


class PylsWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'python', 'pyls')


class DlsWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'd', 'dub', 'run', 'dls')


class ServeDWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__(path, 'd', 'dub', 'run', '-a', 'x86_mscoff',
                         'serve-d')


class DotnetCoreWorkspaceInfo(WorkspaceInfo):
    def __init__(self, path: pathlib.Path) -> None:
        build_dir = HERE.parent.parent / 'build_tasks/omnisharp-roslyn/omnisharp-roslyn'
        omni = build_dir / 'artifacts/publish/OmniSharp.Stdio.Driver/win7-x64/OmniSharp.exe'
        logger.debug(omni)
        super().__init__(path, 'csharp', str(omni), '-lsp', '-e', 'utf-8')

def get_workspaceinfo(path: pathlib.Path) -> Optional[WorkspaceInfo]:
    if path.suffix == '.py':
        found = find_to_ancestors(path, 'setup.py')
        return PylsWorkspaceInfo(found.parent if found else path.parent)
    elif path.suffix == '.d':
        found = find_to_ancestors(path, 'dub.json')
        if found:
            # require dub.json
            return DlsWorkspaceInfo(found.parent)
            #return ServeDWorkspaceInfo(found.parent / 'source')
    elif path.suffix == '.cs':
        found = find_to_ancestors(path, '*.csproj')
        if found:
            # require *.csproj
            return DotnetCoreWorkspaceInfo(found.parent)

    #logger.warn('not implemented: %s', path)
    return None
