import pathlib
import asyncio
from typing import NamedTuple, Optional, List
from . import languageserver
import logging
logger = logging.getLogger(__name__)


class WorkspaceInfo(NamedTuple):
    path: pathlib.Path
    language: str
    cmd: str
    args: List[str] = []

    def launch(self) -> languageserver.LanguageServer:
        return languageserver.LanguageServer(self.path, self.cmd, *self.args)
        if self.language == 'python':
            return languageserver.LanguageServer(self.path, 'pyls')

        raise NotImplementedError(self.language)


def get_python_root(path: pathlib.Path) -> pathlib.Path:
    current = path.parent
    while True:
        if any(f.name == 'setup.py' for f in current.iterdir()):
            return current

        if current == current.parent:
            break
        current = current.parent
    return path


def get_workspace_info(path: pathlib.Path) -> Optional[WorkspaceInfo]:
    if path.suffix == '.py':
        return WorkspaceInfo(get_python_root(path.parent), 'python', 'pyls')

    logger.warn('not implemented: %s', path)
    return None


class Workspace:
    '''
    Workspace単位にLanguageServerを起動する
    '''

    def __init__(self, info: WorkspaceInfo) -> None:
        self.path = info.path
        self.ls = info.launch()

        loop = asyncio.get_running_loop()
        self.async_initialized = loop.create_future()
        asyncio.create_task(self._initialize())

    def shutdown(self) -> None:
        self.ls.shutdown()

    async def _initialize(self):
        await self.ls.async_initialize(self.path)

        self.ls.notify_initialized()

        self.async_initialized.set_result(True)
