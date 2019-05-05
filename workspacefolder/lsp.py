import pathlib
import sys
import asyncio
import logging
from typing import Union, NamedTuple, Optional
from workspacefolder import dispatcher, json_rpc, util, pipestream
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


# }}}


class LanguageServer:
    def __init__(self, cmd, *args):
        self.stream = pipestream.PipeStream(cmd, *args)

    def isenable(self) -> bool:
        return self.stream.p.returncode is None

    def terminate(self) -> None:
        self.stream.terminate()

    async def async_request_initialize(
            self, rootUri: pathlib.Path
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        request = self.stream.dispatcher.create_request(
            'initialize', rootUri=to_uri(rootUri))
        result = await self.stream.async_request(request)

        initialized = json_rpc.JsonRPCNotify('initialized', {})
        self.stream.send_notify(initialized)

        return result

    async def async_document_highlight(self, path: pathlib.Path, line: int,
                                       col: int):
        params = TextDocumentPositionParams(
            TextDocumentIdentifier(to_uri(path)), Position(line, col))
        request = self.stream.dispatcher.create_request(
            'textDocument/documentHighlight', **util.to_dict(params))
        return await self.stream.async_request(request)

    async def async_document_definition(self, path: pathlib.Path, line: int,
                                        col: int):
        params = TextDocumentPositionParams(
            TextDocumentIdentifier(to_uri(path)), Position(line, col))
        request = self.stream.dispatcher.create_request(
            'textDocument/definition', **util.to_dict(params))
        return await self.stream.async_request(request)

    def notify_open(self, path: pathlib.Path) -> None:
        textDocument = TextDocumentItem(to_uri(path), 'python', 1,
                                        path.read_text())
        notify = json_rpc.JsonRPCNotify('textDocument/didOpen',
                                        util.to_dict(textDocument))
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

    async def _ensure_launch(self, _path: str):
        path = pathlib.Path(_path)
        if path.suffix == '.py':
            return await self._launch_pyls(path)

    @dispatcher.rpc_method
    async def notify_document_open(self, path: str) -> None:
        ls = await self._ensure_launch(path)
        if ls:
            ls.notify_open(path)

    @dispatcher.rpc_method
    async def request_document_highlight(self, path: str, line: int,
                                       col: int) -> None:
        ls = await self._ensure_launch(path)
        if ls:
            return await ls.async_document_highlight(path, line, col)

    @dispatcher.rpc_method
    async def request_document_definition(self, path: str, line: int,
                                       col: int) -> None:
        ls = await self._ensure_launch(path)
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
