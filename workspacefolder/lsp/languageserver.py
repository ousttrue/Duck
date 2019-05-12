import pathlib
import json
import asyncio
import sys
import os
from typing import NamedTuple, Optional, List, BinaryIO, Union
from workspacefolder import util
from workspacefolder.rpc import dispatcher, json_rpc, pipestream
import logging
logger = logging.getLogger(__name__)

PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'


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


def to_uri(path: pathlib.Path) -> str:
    return 'file:///' + str(path).replace('\\', '/')


def create_postion_params(path: pathlib.Path, line: int, col: int) -> dict:
    params = TextDocumentPositionParams(TextDocumentIdentifier(to_uri(path)),
                                        Position(line, col))
    return util.to_dict(params)


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
    def __init__(self, language: str, cwd: pathlib.Path, cmd: str,
                 *args) -> None:
        self.language = language
        self.stream = pipestream.PipeStream(cwd, cmd, *args)
        # start stdout reader
        asyncio.create_task(self.stream.process_stdout(self._on_request))
        # start stderr reader
        asyncio.create_task(self.stream.process_stderr(self._on_error))

        self.dispatcher = dispatcher.Dispatcher('PipeStream')

        um = UpstreamMethods(sys.stdout.buffer)
        self.dispatcher.register_methods(um)

    def _on_request(self, rpc) -> None:
        # async_dispatchをスケジュールする
        asyncio.create_task(self.dispatcher.async_dispatch(rpc))

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
        params_dict = create_postion_params(path, line, col)
        request = self.dispatcher.create_request(
            'textDocument/documentHighlight', **params_dict)
        return await self._async_request(request)

    async def async_document_definition(self, path: pathlib.Path, line: int,
                                        col: int):
        params_dict = create_postion_params(path, line, col)
        request = self.dispatcher.create_request('textDocument/definition',
                                                 **params_dict)
        return await self._async_request(request)

    async def async_document_completion(self, path: pathlib.Path, line: int,
                                        col: int):
        params_dict = create_postion_params(path, line, col)
        request = self.dispatcher.create_request('textDocument/completion',
                                                 **params_dict)
        return await self._async_request(request)

    async def async_document_hover(self, path: pathlib.Path, line: int,
                                   col: int):
        params_dict = create_postion_params(path, line, col)
        request = self.dispatcher.create_request('textDocument/hover',
                                                 **params_dict)
        return await self._async_request(request)

    async def async_document_references(self, path: pathlib.Path, line: int,
                                        col: int):
        params_dict = create_postion_params(path, line, col)
        params_dict['context'] = {'includeDeclaration': True}
        request = self.dispatcher.create_request('textDocument/references',
                                                 **params_dict)
        return await self._async_request(request)

    def notify_initialized(self):
        notify = json_rpc.JsonRPCNotify('initialized', {})
        self.stream.send_notify(notify)

    def notify_document_open(self, version: int, path: pathlib.Path,
                             text: str) -> None:

        params = DidOpenTextDocumentParams(
            TextDocumentItem(to_uri(path), self.language, version, text))

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
