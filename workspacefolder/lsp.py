import pathlib
import json
import sys
import asyncio
import subprocess
import logging
from typing import Union, IO, Any, NamedTuple
from workspacefolder import dispatcher, http, json_rpc
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def to_uri(path: pathlib.Path) -> str:
    return 'file:///' + str(path).replace('\\', '/')


class TextDocumentItem(NamedTuple):
    uri: str
    languageId: str
    version: int
    text: str


async def process_child_stdout(c: IO[Any], push):
    loop = asyncio.get_running_loop()

    while True:
        b = await loop.run_in_executor(None, c.read, 1)
        if not b:
            logger.debug(b'stdout break\n')
            break
        push(b[0])


async def process_child_stderr(c: IO[Any]):
    loop = asyncio.get_running_loop()

    while True:
        line = await loop.run_in_executor(None, c.readline)
        if not line:
            logger.debug(b'stderr break\n')
            break


class Pyls:
    def __init__(self):
        self.cmd = 'pyls'
        self.args = []
        self.p = None
        self.splitter = http.HttpSplitter()
        self.dispatcher = dispatcher.Dispatcher()

    def terminate(self):
        self.p.stdin.close()
        self.p.stdout.close()
        self.p.stderr.close()
        # self.p.terminate()

    def _send_body(self, body: bytes):
        logger.debug(body)
        header = f'Content-Length: {len(body)}\r\n\r\n'
        self.p.stdin.write(header.encode('ascii'))
        self.p.stdin.write(body)
        self.p.stdin.flush()

    def _send_request(self, request: json_rpc.JsonRPCRequest):

        request_json = json.dumps(request._asdict())
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)

    def _send_notify(self, notify: json_rpc.JsonRPCNotify):

        request_json = json.dumps(notify._asdict())
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)

    async def async_launch(self, rootUri: pathlib.Path):
        # create process
        self.p = subprocess.Popen([self.cmd] + self.args,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)

        # start pipe reader
        if self.p.stderr:
            asyncio.create_task(process_child_stderr(self.p.stderr))
        if self.p.stdout:
            asyncio.create_task(process_child_stdout(self.p.stdout, self.push))

        await self.async_request_initialize(rootUri)

    async def _async_request(
            self, request: json_rpc.JsonRPCRequest
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        self._send_request(request)
        result = await self.dispatcher.wait_request(request)
        logger.debug(result)
        return result

    async def async_request_initialize(
            self, rootUri: pathlib.Path
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        request = self.dispatcher.create_request('initialize',
                                                 rootUri=to_uri(rootUri))
        result = await self._async_request(request)

        initialized = json_rpc.JsonRPCNotify('initialized', {})
        self._send_notify(initialized)

        return result

    def notify_open(self, path: pathlib.Path) -> None:
        textDocument = TextDocumentItem(to_uri(path), 'python', 1,
                                        path.read_text())
        notify = json_rpc.JsonRPCNotify('textDocument/didOpen',
                                        textDocument._asdict())
        self._send_notify(notify)

    def push(self, b: int) -> None:
        request = self.splitter.push(b)
        if request:
            self.dispatcher.dispatch_jsonrpc(request.body)


class LanguageServerManager:
    def __init__(self):
        self.pyls = None

    @dispatcher.rpc_method
    def document_open(self, path: str) -> None:
        asyncio.create_task(self.async_document_open(pathlib.Path(path)))

    async def ensure_launch(self, path: pathlib.Path):
        if not self.pyls or (self.pyls.p
                             and self.pyls.p.returncode is not None):
            self.pyls = Pyls()
            await self.pyls.async_launch(path.parent)

    async def async_document_open(self, path: pathlib.Path) -> None:
        await self.ensure_launch(path)
        await asyncio.sleep(2)
        self.pyls.notify_open(path)
        logger.debug('done')


# {{{
if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    lsm = LanguageServerManager()

    async def run():
        await lsm.async_document_open(pathlib.Path(__file__))
        lsm.pyls.terminate()

    asyncio.run(run())
# }}}
