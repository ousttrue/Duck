import pathlib
import json
import sys
import os
import asyncio
import logging
from typing import Union, NamedTuple, Optional, BinaryIO, List, Any
from workspacefolder import dispatcher, json_rpc, util, pipestream, http
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def to_uri(path: pathlib.Path) -> str:
    return 'file:///' + str(path).replace('\\', '/')


# types {{{
class TextDocumentItem(NamedTuple):
    uri: str
    languageId: str
    version: int
    text: str


class Position(NamedTuple):
    line: int
    character: int


class Range(NamedTuple):
    start: Position
    end: Position


class TextDocumentIdentifier(NamedTuple):
    uri: str
    version: Optional[int] = None


class TextDocumentContentChangeEvent(NamedTuple):
    text: str
    range: Optional[Range] = None
    rangeLength: Optional[int] = None


class TextDocumentPositionParams(NamedTuple):
    textDocument: TextDocumentIdentifier
    position: Position


class DidOpenTextDocumentParams(NamedTuple):
    textDocument: TextDocumentItem


class DidChangeTextDocumentParams(NamedTuple):
    textDocument: TextDocumentIdentifier
    contentChanges: List[TextDocumentContentChangeEvent]


# }}}

PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'


class UpstreamMethods:
    def __init__(self, f: BinaryIO) -> None:
        self.f = f

    @dispatcher.rpc_method_with_name(PUBLISH_DIAGNOSTICS)
    async def diagnostics(self, **kw):
        notify = json_rpc.JsonRPCNotify(PUBLISH_DIAGNOSTICS, kw)
        body = json.dumps(util.to_dict(notify))
        self.f.write(
            f'Content-Length: {len(body)}\r\n\r\n{body}'.encode('utf-8'))


class LanguageServer:
    def __init__(self, cmd, *args):
        self.stream = pipestream.PipeStream(cmd, *args)
        # start stdout reader
        asyncio.create_task(self.stream.process_stdout(self._on_request))
        # start stderr reader
        asyncio.create_task(self.stream.process_stderr(self._on_error))

        self.dispatcher = dispatcher.Dispatcher('PipeStream')

        um = UpstreamMethods(sys.stdout.buffer)
        self.dispatcher.register_methods(um)

    def _on_request(self, request: http.HttpRequest) -> None:
        # async_dispatchをスケジュールする
        asyncio.create_task(self.dispatcher.async_dispatch(request.body))

    def _on_error(self, line: bytes) -> None:
        # logging
        logger.error(line)

    def shutdown(self) -> None:
        self.stream.shutdown()

    async def _async_request(
            self, request: json_rpc.JsonRPCRequest
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        '''
        JSON-RPC Request を送信し、対応する Response が返るのを待つ
        '''
        self.stream.send_request(request)
        result = await self.dispatcher.wait_request(request)
        logger.debug('%d->%s', request.id, json.dumps(result, indent=2))
        return result

    async def async_initialize(
            self, rootUri: pathlib.Path
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        request = self.dispatcher.create_request(
            'initialize',
            rootUri=to_uri(rootUri),
            rootPath=str(rootUri),
            trace='off',
            processId=os.getpid(),
            capabilities={'workspace': {
                'applyEdit': True
            }})
        return await self._async_request(request)

    async def async_document_highlight(self, path: pathlib.Path, line: int,
                                       col: int):
        params = TextDocumentPositionParams(
            TextDocumentIdentifier(to_uri(path)), Position(line, col))
        request = self.dispatcher.create_request(
            'textDocument/documentHighlight', **util.to_dict(params))
        return await self._async_request(request)

    async def async_document_definition(self, path: pathlib.Path, line: int,
                                        col: int):
        params = TextDocumentPositionParams(
            TextDocumentIdentifier(to_uri(path)), Position(line, col))
        request = self.dispatcher.create_request('textDocument/definition',
                                                 **util.to_dict(params))
        return await self._async_request(request)

    def notify_initialized(self):
        notify = json_rpc.JsonRPCNotify('initialized', {})
        self.stream.send_notify(notify)

    def notify_document_open(self, version: int, path: pathlib.Path, text: str) -> None:

        params = DidOpenTextDocumentParams(
            TextDocumentItem(to_uri(path), 'python', version, text))

        notify = json_rpc.JsonRPCNotify('textDocument/didOpen',
                                        util.to_dict(params))
        self.stream.send_notify(notify)

    def notify_document_change(self, version: int, path: pathlib.Path,
                      text: str) -> None:
        params = DidChangeTextDocumentParams(
            TextDocumentIdentifier(to_uri(path), version),
            [TextDocumentContentChangeEvent(text)])

        notify = json_rpc.JsonRPCNotify('textDocument/didChange',
                                        util.to_dict(params))
        self.stream.send_notify(notify)


class WorkspaceInfo(NamedTuple):
    path: pathlib.Path
    language: str


def get_workspace_info(path: pathlib.Path) -> WorkspaceInfo:
    if path.suffix == '.py':
        # ToDo: detect project root
        return WorkspaceInfo(path.parent, 'python')

    logger.warn('not implemented: %s', path)
    return None


def create_ls(language: str) -> LanguageServer:
    if language == 'python':
        return LanguageServer('pyls')

    raise NotImplemented(language)


class Workspace:
    '''
    Workspace単位にLanguageServerを起動する
    '''

    def __init__(self, path: pathlib.Path, language: str) -> None:
        self.path = path
        self.ls = create_ls(language)

        loop = asyncio.get_running_loop()
        self.async_initialized = loop.create_future()
        asyncio.create_task(self._initialize())

    def shutdown(self) -> None:
        self.ls.shutdown()

    async def _initialize(self):
        await self.ls.async_initialize(self.path)

        self.ls.notify_initialized()

        self.async_initialized.set_result(True)


class Document:
    '''
    複数のドキュメントがひとつのWorkspaceに所属する
    '''

    def __init__(self, path: pathlib.Path, ws: Workspace, text: str) -> None:
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


##############################################################################
# interface
##############################################################################
class LspInterface:
    '''
    RPC methods that export to vimplugin

    処理は Document に委譲する。
    path ごとに Document が存在する。
    '''

    def __init__(self) -> None:
        self.workspace_map: Dict[pathlib.Path, Workspace] = {}
        self.document_map: Dict[pathlib.Path, Document] = {}

    def shutdown(self) -> None:
        for k, v in self.workspace_map.items():
            v.shutdown()
        self.workspace_map.clear()
        self.document_map.clear()

    def _get_or_create_workspace(self, info: WorkspaceInfo) -> Workspace:
        ws = self.workspace_map.get(info.path)
        if not ws:
            ws = Workspace(info.path, info.language)
            self.workspace_map[info.path] = ws
        return ws

    def _get_or_create_document(self, path: pathlib.Path,
                                text='') -> Optional[Document]:
        document = self.document_map.get(path)
        if not document:
            # creae workspace
            workspace_info = get_workspace_info(path)
            if not workspace_info:
                return None

            ws = self._get_or_create_workspace(workspace_info)
            self.workspace_map[workspace_info.path] = ws

            # create document
            document = Document(path, ws, text)
            self.document_map[path] = document

        return document

    @dispatcher.rpc_method
    async def notify_document_open(self, _path: str, text: str) -> None:
        path = pathlib.Path(_path)
        document = self._get_or_create_document(path)
        if document:
            await document.ws.async_initialized

    @dispatcher.rpc_method
    async def notify_document_change(self, _path: str, text: str) -> None:
        path = pathlib.Path(_path)
        document = self._get_or_create_document(path)
        if document:
            await document.notify_change(text)

    @dispatcher.rpc_method
    async def request_document_highlight(self, _path: str, line: int,
                                         col: int) -> Any:
        path = pathlib.Path(_path)
        document = self._get_or_create_document(path)
        if document:
            return await document.async_highlight(line, col)

    @dispatcher.rpc_method
    async def request_document_definition(self, _path: str, line: int,
                                          col: int) -> Any:
        path = pathlib.Path(_path)
        document = self._get_or_create_document(path)
        if document:
            return await document.async_definition(line, col)


# debug {{{
if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    lspi = LspInterface()

    async def run():
        path = pathlib.Path(__file__)
        text = path.read_text('utf-8')

        # ws = Workspace(path.parent, 'python')
        # await ws.async_initialized
        #
        # documen = Document(path, ws, text)

        await lspi.notify_document_open(path, text)

        # wait diagnostics
        await asyncio.sleep(2)

        await lspi.request_document_highlight(pathlib.Path(__file__), 0, 0)
        await lspi.request_document_definition(pathlib.Path(__file__), 0, 0)

        await lspi.notify_document_change(path, text)

        lspi.shutdown()
        logger.debug('done')

    asyncio.run(run())
# }}}
