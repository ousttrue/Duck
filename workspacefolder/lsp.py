import pathlib
import sys
import asyncio
import subprocess
import logging
from typing import Union
from workspacefolder import dispatcher, http, json_rpc
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


async def process_child_stdout(c: asyncio.StreamReader, push):
    while True:
        b = await c.read(1)
        if not b:
            logger.debug(b'stdout break\n')
            break
        push(b[0])


async def process_child_stderr(c: asyncio.StreamReader):
    while True:
        line = await c.readline()
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

    def send_request(self, request: bytes):
        logger.debug(request)
        header = f'Content-Length: {len(request)}\r\n\r\n'
        self.p.stdin.write(header.encode('ascii'))
        self.p.stdin.write(request)

    async def async_launch(self, rootUri: pathlib.Path):
        logger.debug("async_launch")
        # create process
        self.p = await asyncio.create_subprocess_exec(self.cmd,
                                                      *self.args,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE,
                                                      stdin=subprocess.PIPE)
        logger.debug('create process: %s', self.cmd)

        # start pipe reader
        if self.p.stderr:
            asyncio.create_task(process_child_stderr(self.p.stderr))
        if self.p.stdout:
            asyncio.create_task(process_child_stdout(self.p.stdout, self.push))

        result = await self.async_initialize(rootUri)
        logger.debug(result)

    async def async_initialize(self, rootUri: pathlib.Path) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        params = {
                'rootUrih': str(rootUri)
                }
        return await self.dispatcher.async_request(self.p.stdin, 'initialize',
                                                   **params)

    async def async_open(self, path: pathlib.Path) -> None:
        logger.debug(path)

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

    async def get_or_launch(self, path: pathlib.Path) -> Pyls:
        if not self.pyls or (self.pyls.p
                             and self.pyls.p.returncode is not None):
            self.pyls = Pyls()
            await self.pyls.async_launch(path.parent)
        return self.pyls

    async def async_document_open(self, path: pathlib.Path) -> None:
        pyls = await self.get_or_launch(path)
        await pyls.async_open(path)


# {{{
if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    lsm = LanguageServerManager()

    async def run():
        await lsm.async_document_open(pathlib.Path(__file__))
        await lsm.pyls.p.wait()

    asyncio.run(run())
# }}}
