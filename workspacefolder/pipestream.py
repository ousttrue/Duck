import json
import asyncio
import subprocess
import logging
from typing import Any, IO, Union
from workspacefolder import http, dispatcher, json_rpc, util
logger = logging.getLogger(__name__)


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


class PipeStream:
    def __init__(self, cmd, *args):
        logger.debug('%s %s', cmd, args)
        self.cmd = cmd
        self.args = args
        self.p = None
        self.splitter = http.HttpSplitter()
        self.dispatcher = dispatcher.Dispatcher()

        # create process
        self.p = subprocess.Popen([self.cmd] + list(self.args),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
        # start pipe reader
        if self.p.stderr:
            asyncio.create_task(process_child_stderr(self.p.stderr))
        if self.p.stdout:
            asyncio.create_task(process_child_stdout(self.p.stdout, self.push))

    def terminate(self):
        self.p.stdin.close()
        self.p.stdout.close()
        self.p.stderr.close()
        # self.p.terminate()

    def _send_body(self, body: bytes):
        header = f'Content-Length: {len(body)}\r\n\r\n'
        self.p.stdin.write(header.encode('ascii'))
        self.p.stdin.write(body)
        self.p.stdin.flush()

    def _send_request(self, request: json_rpc.JsonRPCRequest):

        d = util.to_dict(request)
        logger.debug('<--request: %s', d)
        request_json = json.dumps(d)
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)

    def send_notify(self, notify: json_rpc.JsonRPCNotify):
        logger.debug('<--notify: %s', notify.method)

        request_json = json.dumps(util.to_dict(notify))
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)

    def push(self, b: int) -> None:
        request = self.splitter.push(b)
        if request:
            self.dispatcher.dispatch_jsonrpc(request.body)

    async def async_request(
            self, request: json_rpc.JsonRPCRequest
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:
        self._send_request(request)
        result = await self.dispatcher.wait_request(request)
        logger.debug('%d->%s', request.id, result)
        return result
