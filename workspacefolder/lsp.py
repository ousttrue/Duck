import pathlib
import json
import sys
import os
import asyncio
import logging
from typing import Union, NamedTuple, Optional
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


class TextDocumentIdentifier(NamedTuple):
    uri: str
    version: Optional[int] = None


class TextDocumentPositionParams(NamedTuple):
    textDocument: TextDocumentIdentifier
    position: Position


class DidOpenTextDocumentParams(NamedTuple):
    textDocument: TextDocumentItem


# }}}


class LanguageServer:
    def __init__(self, cmd, *args):
        self.initialized = False
        self.stream = pipestream.PipeStream(cmd, *args)
        # start stdout reader
        asyncio.create_task(self.stream.process_stdout(self._on_request))
        # start stderr reader
        asyncio.create_task(self.stream.process_stderr(self._on_error))

        self.dispatcher = dispatcher.Dispatcher('PipeStream')

    def _on_request(self, request: http.HttpRequest) -> None:
        # async_dispatchをスケジュールする
        asyncio.create_task(self.dispatcher.async_dispatch(request.body))

    def _on_error(self, line: bytes) -> None:
        # logging
        logger.error(line)

    def isenable(self) -> bool:
        if not self.initialized:
            return False
        if self.stream.p.returncode is not None:
            return False
        return True

    def terminate(self) -> None:
        self.stream.terminate()

    async def _async_request(
            self, request: json_rpc.JsonRPCRequest
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        self.stream.send_request(request)
        result = await self.dispatcher.wait_request(request)
        logger.debug('%d->%s', request.id, json.dumps(result, indent=2))
        return result

    async def async_request_initialize(
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
        result = await self._async_request(request)

        initialized = json_rpc.JsonRPCNotify('initialized', {})
        self.stream.send_notify(initialized)

        self.initialized = True

        return result

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

    def notify_open(self, path: pathlib.Path) -> None:

        params = DidOpenTextDocumentParams(
            TextDocumentItem(to_uri(path), 'python', 1,
                             path.read_text(encoding='utf-8')))

        notify = json_rpc.JsonRPCNotify('textDocument/didOpen',
                                        util.to_dict(params))
        self.stream.send_notify(notify)


class LanguageServerManager:
    def __init__(self):
        self.pyls = None

    async def _launch_pyls(self, path: pathlib.Path) -> LanguageServer:
        if self.pyls:
            if self.pyls.isenable():
                return self.pyls

        self.pyls = LanguageServer('pyls')
        await self.pyls.async_request_initialize(path.parent)
        return self.pyls

    async def _ensure_launch(self, path: pathlib.Path):
        if path.suffix == '.py':
            return await self._launch_pyls(path)

    def _get_ls(self, path: pathlib.Path):
        if path.suffix == '.py':
            if self.pyls and self.pyls.isenable():
                return self.pyls

    @dispatcher.rpc_method
    async def notify_document_open(self, _path: str) -> None:
        path = pathlib.Path(_path)
        ls = await self._ensure_launch(path)
        if ls:
            ls.notify_open(path)

    @dispatcher.rpc_method
    async def request_document_highlight(self, _path: str, line: int,
                                         col: int) -> None:
        path = pathlib.Path(_path)
        ls = self._get_ls(path)
        if ls:
            return await ls.async_document_highlight(path, line, col)

    @dispatcher.rpc_method
    async def request_document_definition(self, _path: str, line: int,
                                          col: int) -> None:
        path = pathlib.Path(_path)
        ls = self._get_ls(path)
        if ls:
            return await ls.async_document_definition(path, line, col)


# debug {{{
if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    lsm = LanguageServerManager()

    async def run():
        await lsm.notify_document_open(pathlib.Path(__file__))
        await lsm.request_document_highlight(pathlib.Path(__file__), 0, 0)
        await lsm.request_document_definition(pathlib.Path(__file__), 60, 35)

        lsm.pyls.terminate()
        logger.debug('done')

    asyncio.run(run())
# }}}
