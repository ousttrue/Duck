import json
import asyncio
import subprocess
import logging
from . import http, json_rpc
from workspacefolder import util
logger = logging.getLogger(__name__)


class PipeStream:
    '''
    Pipe上に
    HttpLike(StatusLine抜きの,Content-Lengthヘッダを必須とするメッセージ)な
    経路を確立する。
    '''

    def __init__(self, cwd, cmd, *args):
        cmdline = [cmd] + list(args)
        logger.debug('%s', cmdline)
        self.p = subprocess.Popen(cmdline,
                                  cwd=cwd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
        self.splitter = http.HttpSplitter()

    def shutdown(self):
        self.p.stdin.close()
        self.p.stdout.close()
        self.p.stderr.close()
        self.p.terminate()

    async def process_stdout(self, on_request) -> None:
        r = self.p.stdout
        loop = asyncio.get_running_loop()

        while True:
            b = await loop.run_in_executor(None, r.read, 1)
            if not b:
                logger.debug(b'stdout break\n')
                break

            # split to http like message
            request = self.splitter.push(b[0])
            if request:
                body = request.body
                rpc = json.loads(body)
                if 'id' in rpc:
                    logger.debug('%s->%s', rpc['id'], util.indent_json(body))
                else:
                    logger.debug('-->%s', util.indent_json(body))
                on_request(rpc)

    async def process_stderr(self, on_error):
        r = self.p.stderr
        loop = asyncio.get_running_loop()

        while True:
            line = await loop.run_in_executor(None, r.readline)
            if not line:
                logger.debug(b'stderr break\n')
                break

            on_error(line)

    def _send_body(self, body: bytes):
        header = f'Content-Length: {len(body)}\r\n\r\n'
        self.p.stdin.write(header.encode('ascii'))
        self.p.stdin.write(body)
        self.p.stdin.flush()

    def send_request(self, request: json_rpc.JsonRPCRequest):
        d = util.to_dict(request)
        request_json = json.dumps(d, indent=2)
        logger.debug('<-%d%s', request.id, request_json)
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)

    def send_notify(self, notify: json_rpc.JsonRPCNotify):
        d = util.to_dict(notify)
        request_json = json.dumps(d, indent=2)
        logger.debug('<--%s', request_json)
        request_bytes = request_json.encode('utf-8')
        self._send_body(request_bytes)
