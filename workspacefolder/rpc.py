import asyncio
import sys
import json
import io
import logging
from typing import BinaryIO
from workspacefolder import http, dispatcher, json_rpc, lsp
logger = logging.getLogger(__name__)


async def start_stdin_reader(r: BinaryIO, w: BinaryIO, dispatcher) -> None:
    splitter = http.HttpSplitter()

    loop = asyncio.get_event_loop()

    # fix BOM from powershell pipe
    # async read a byte.
    # use threadpool executor for stdin of Windows
    bom_check = await loop.run_in_executor(None, r.read, 3)
    if not bom_check:
        logger.debug('stdin break')
        return
    if bom_check != b'\xef\xbb\xbf':  # BOM
        for b in bom_check:
            splitter.push(b)

    while True:
        # async read a byte.
        # use threadpool executor for stdin of Windows
        read_byte: bytes = await loop.run_in_executor(None, r.read, 1)
        if not read_byte:
            logger.debug('stdin break')
            break
        b = read_byte[0]

        request = splitter.push(b)
        if request:
            body = dispatcher.dispatch_jsonrpc(request.body)
            if body:
                w.write(b'Content-Length: ')
                w.write(str(len(body)).encode('ascii'))
                w.write(b'\r\n\r\n')
                w.write(body)


def execute(parsed):
    d = dispatcher.Dispatcher()

    lsm = lsp.LanguageServerManager()
    d.register_methods(lsm)

    if parsed.debug:
        d.register_dbug_methods()

    # block until stdin break
    asyncio.run(start_stdin_reader(sys.stdin.buffer, sys.stdout.buffer, d))


# {{{
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

    import unittest

    class RpcTest(unittest.TestCase):
        def setUp(self):
            self.request_id = 1

        def get_request_id(self):
            request_id = self.request_id
            self.request_id += 1
            return request_id

        def create_request(self, method, *args):
            rpc = {
                'jsonrpc': '2.0',
                'method': method,
                'params': args,
                'id': self.get_request_id(),
            }
            body = json.dumps(rpc).encode('utf-8')
            return f'Content-Length: {len(body)}\r\n\r\n'.encode(
                'ascii') + body

        def test_Rpc(self):
            r = io.BytesIO()
            r.write(BOM)
            r.write(self.create_request('hello', 'world'))
            r.write(self.create_request('add', 1, 2))
            r.seek(0, 0)

            w = io.BytesIO()
            d = dispatcher.Dispatcher()

            d.register_dbug_methods()

            asyncio.run(start_stdin_reader(r, w, d))

            results = [r for r in http.split(w.getvalue())]

            # hello
            msg = json_rpc.parse(results[0][1])
            self.assertTrue(isinstance(msg, json_rpc.JsonRPCResponse))
            self.assertEqual('hello world', msg.result)

            # add
            msg = json_rpc.parse(results[1][1])
            self.assertTrue(isinstance(msg, json_rpc.JsonRPCResponse))
            self.assertEqual(3, msg.result)

    unittest.main()
    # }}}
