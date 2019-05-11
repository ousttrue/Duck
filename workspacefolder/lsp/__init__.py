import pathlib
import logging
from typing import Optional, Dict, Iterable
from . import workspace, document
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

    def get_or_create_document(self, path: pathlib.Path
                               ) -> Optional[document.Document]:
        doc = self.document_map.get(path)
        if not doc:
            ws = self._get_or_create_workspace(path)
            if not ws:
                return None
            self.workspace_map[ws.path] = ws

            # create document
            doc = document.Document(path, ws)
            self.document_map[path] = doc

        return doc
