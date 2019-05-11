import pathlib
import asyncio
from typing import Any
from . import workspace


class Document:
    '''
    複数のドキュメントがひとつのWorkspaceに所属する
    '''

    def __init__(self, path: pathlib.Path, ws: workspace.Workspace,
                 text: str) -> None:
        self.path = path
        self.ws = ws
        self.version = 1
        self.text = text
        asyncio.create_task(self._initialize(text))

    async def _initialize(self, text):
        await self.ws.async_initialized
        self.ws.ls.notify_document_open(self.version, self.path, text)

    async def notify_change(self, text: str) -> None:
        if text == self.text:
            # no change
            return

        await self.ws.async_initialized
        self.version += 1
        self.text = text
        self.ws.ls.notify_document_change(self.version, self.path, text)

    async def async_highlight(self, line: int, col: int) -> Any:
        await self.ws.async_initialized
        return await self.ws.ls.async_document_highlight(self.path, line, col)

    async def async_definition(self, line: int, col: int) -> Any:
        await self.ws.async_initialized
        return await self.ws.ls.async_document_definition(self.path, line, col)

    async def async_completion(self, line: int, col: int) -> Any:
        await self.ws.async_initialized
        return await self.ws.ls.async_document_completion(self.path, line, col)
