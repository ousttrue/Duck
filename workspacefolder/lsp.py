import asyncio
import logging
from workspacefolder import dispatcher
logger = logging.getLogger(__name__)


class Pyls:
    def __init__(self):
        pass

    async def async_launch(self):
        logger.debug("async_launch")

    async def async_open(self, path) -> None:
        logger.debug(path)


class LanguageServerManager:
    def __init__(self):
        self.pyls = None

    @dispatcher.rpc_method
    def document_open(self, path) -> None:
        asyncio.create_task(self.async_document_open(path))

    async def get_or_launch(self, path):
        if not self.pyls:
            self.pyls = Pyls()
            await self.pyls.async_launch()
        return self.pyls

    async def async_document_open(self, path) -> None:
        pyls = await self.get_or_launch(path)
        await pyls.async_open(path)
