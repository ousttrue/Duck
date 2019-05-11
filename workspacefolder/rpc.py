import asyncio
import sys
import json
import io
import logging
from typing import BinaryIO
from workspacefolder import http, dispatcher, json_rpc, lsp
logger = logging.getLogger(__name__)


async def async_dispatch(dispatcher, request, w):
    rpc = json.loads(request.body)
    body = await dispatcher.async_dispatch(rpc)
    if body:
        bio = io.BytesIO()
        bio.write(b'Content-Length: ')
        bio.write(str(len(body)).encode('ascii'))
        bio.write(b'\r\n\r\n')
        bio.write(body)
        bio.seek(0)
        w.write(bio.getvalue())
        w.flush()


BOM = b'\xef\xbb\xbf'


async def start_stdin_reader(r: BinaryIO, w: BinaryIO, dispatcher) -> None:
    splitter = http.HttpSplitter()

    loop = asyncio.get_event_loop()

    # fix BOM from powershell pipe
    # async read a byte.
    # use threadpool executor for stdin of Windows
    bom_check = await loop.run_in_executor(None, r.read, 3)
    if not bom_check:
        logger.debug(b'stdin break')
        return
    if bom_check != BOM:  # BOM
        for b in bom_check:
            splitter.push(b)

    while True:
        # async read a byte.
        # use threadpool executor for stdin of Windows
        read_byte: bytes = await loop.run_in_executor(None, r.read, 1)
        if not read_byte:
            logger.debug(b'stdin break')
            break
        b = read_byte[0]

        request = splitter.push(b)
        if request:
            asyncio.create_task(async_dispatch(dispatcher, request, w))


def setup_parser(parser):
    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')


def execute(parsed):
    logging.info('##################################################')

    d = dispatcher.Dispatcher(b'RPC')

    lspi = lsp.LspInterface()
    d.register_methods(lspi)

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
            d = dispatcher.Dispatcher('RPCTest')

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
