import pathlib
import logging
from typing import Optional, Any, Dict
from . import workspace, document
from workspacefolder.rpc import dispatcher
logger = logging.getLogger(__name__)


class LspInterface:
    '''
    RPC methods that export to vimplugin

    処理は Document に委譲する。
    path ごとに Document が存在する。
    '''

    def __init__(self) -> None:
        self.workspace_map: Dict[pathlib.Path, workspace.Workspace] = {}
        self.document_map: Dict[pathlib.Path, document.Document] = {}

    def shutdown(self) -> None:
        for k, v in self.workspace_map.items():
            v.shutdown()
        self.workspace_map.clear()
        self.document_map.clear()

    def _get_or_create_workspace(self, path: pathlib.Path
                                 ) -> Optional[workspace.Workspace]:
        info = workspace.get_workspace_info(path)
        if not info:
            return None

        ws = self.workspace_map.get(info.path)
        if not ws:
            ws = workspace.Workspace(info)
            self.workspace_map[info.path] = ws
        return ws

    def _get_or_create_document(self, path: pathlib.Path,
                                text='') -> Optional[document.Document]:
        doc = self.document_map.get(path)
        if not doc:
            ws = self._get_or_create_workspace(path)
            if not ws:
                return None
            self.workspace_map[ws.path] = ws

            # create document
            doc = document.Document(path, ws, text)
            self.document_map[path] = doc

        return doc

    @dispatcher.rpc_method
    async def notify_document_open(self, _path: str, text: str) -> None:
        path = pathlib.Path(_path)
        doc = self._get_or_create_document(path, text)
        if doc:
            await doc.ws.async_initialized

    @dispatcher.rpc_method
    async def notify_document_change(self, _path: str, text: str) -> None:
        path = pathlib.Path(_path)
        doc = self._get_or_create_document(path)
        if doc:
            await doc.notify_change(text)

    @dispatcher.rpc_method
    async def request_document_highlight(self, _path: str, line: int,
                                         col: int) -> Any:
        path = pathlib.Path(_path)
        doc = self._get_or_create_document(path)
        if doc:
            return await doc.async_highlight(line, col)

    @dispatcher.rpc_method
    async def request_document_definition(self, _path: str, line: int,
                                          col: int) -> Any:
        path = pathlib.Path(_path)
        doc = self._get_or_create_document(path)
        if doc:
            return await doc.async_definition(line, col)

    @dispatcher.rpc_method
    async def request_document_completion(self, _path: str, line: int,
                                          col: int) -> Any:
        path = pathlib.Path(_path)
        doc = self._get_or_create_document(path)
        if doc:
            return await doc.async_completion(line, col)
