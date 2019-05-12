import asyncio
import logging
from . import workspaceinfo
logger = logging.getLogger(__name__)


class Workspace:
    '''
    Launch LanguageServer for each Workspace(project root)
    '''

    def __init__(self, info: workspaceinfo.WorkspaceInfo) -> None:
        self.info = info
        self.ls = info.launch()

        loop = asyncio.get_running_loop()
        self.async_initialized = loop.create_future()
        asyncio.create_task(self._initialize())

    def shutdown(self) -> None:
        self.ls.shutdown()

    async def _initialize(self) -> None:
        # request lsp initialize
        await self.ls.async_initialize(self.info.path)
        # notify lsp initialized
        self.ls.notify_initialized()
        # done
        self.async_initialized.set_result(True)
