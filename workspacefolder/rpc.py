import asyncio
import sys
import json
import io
import logging
from typing import BinaryIO, Dict, Any, NamedTuple, Union
if __name__ == '__main__':
    import http
else:
    from . import http
logger = logging.getLogger(__name__)

BOM = b'\xef\xbb\xbf'


class JsonRPCRequest(NamedTuple):
    method: bytes
    params: Union[list, dict]
    id: int
    jsonrpc: bytes = b'2.0'


class JsonRPCResponse(NamedTuple):
    id: int
    result: Any
    jsonrpc: bytes = b'2.0'


class JsonRPCError(NamedTuple):
    id: int
    error: str
    jsonrpc: bytes = b'2.0'


class JsonRPCNotify(NamedTuple):
    method: bytes
    params: Union[list, dict]
    jsonrpc: bytes = b'2.0'


def to_rpc(
        src: bytes
) -> Union[JsonRPCRequest, JsonRPCResponse, JsonRPCError, JsonRPCNotify]:
    rpc = json.loads(src)

    if rpc['jsonrpc'] != '2.0':
        raise ValueError('jsonrpc is not 2.0')

    if 'method' in rpc:
        if 'id' in rpc:
            return JsonRPCRequest(**rpc)
        else:
            return JsonRPCNotify(**rpc)
    elif 'result' in rpc:
        return JsonRPCResponse(**rpc)
    elif 'error' in rpc:
        return JsonRPCError(**rpc)
    else:
        raise ValueError(src)


class RpcDispatcher:
    def __init__(self) -> None:
        self.splitter = http.HttpSplitter()
        self.splitter.append_callback(self.on_http)
        self.method_map: Dict[str, Any] = {}

    def register(self, name: bytes, callback) -> None:
        self.method_map[name] = callback

    def register_dbug_methods(self) -> None:
        # hello
        def hello(target: str):
            return 'hello ' + target

        self.register('hello', hello)

        # add
        def add(a, b):
            return a + b

        self.register('add', add)

    def on_http(self, request: http.HttpRequest) -> None:
        logger.debug(request.body)
        message = to_rpc(request.body)
        logger.debug(message)

        if isinstance(message, JsonRPCRequest):
            callback = self.method_map.get(message.method)
            if not callback:
                raise ValueError(f'{message.method} not found')

            if isinstance(message.params, dict):
                result = callback(**message.params)
                self.send_response(message.id, result)

            elif isinstance(message.params, list):
                result = callback(*message.params)
                self.send_response(message.id, result)

            else:
                raise ValueError('params not dict or list')

        elif isinstance(message, JsonRPCNotify):
            raise NotImplementedError()

        elif isinstance(message, JsonRPCResponse):
            raise NotImplementedError()

        elif isinstance(message, JsonRPCError):
            raise NotImplementedError()

        else:
            raise ValueError()

    def send_response(self, id: int, value: Any) -> None:
        body = json.dumps({
            'jsonrpc': '2.0',
            'id': id,
            'result': value
        }).encode('utf-8')

        self.w.write(b'Content-Length: ')
        self.w.write(str(len(body)).encode('ascii'))
        self.w.write(b'\r\n\r\n')
        self.w.write(body)

    async def start_stdin_reader(self, r: BinaryIO, w: BinaryIO) -> None:
        self.w = w
        loop = asyncio.get_event_loop()
        # stdin = sys.stdin.buffer
        bom_check = bytearray()
        while True:
            b: bytes = await loop.run_in_executor(None, r.read, 1)
            if not b:
                logger.debug('stdin break')
                break

            if bom_check is not None:
                # for powershell pipe
                bom_check.append(b[0])
                if len(bom_check) == 3:
                    if bytes(bom_check) != BOM:
                        for b in bom_check:
                            self.splitter.push(b)
                    bom_check = None

            else:
                self.splitter.push(b[0])


def execute(parsed):
    dispatcher = RpcDispatcher()

    if parsed.debug:
        dispatcher.register_dbug_methods()

    # block until stdin break
    asyncio.run(
        dispatcher.start_stdin_reader(sys.stdin.buffer, sys.stdout.buffer))


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
            d = RpcDispatcher()

            d.register_dbug_methods()

            asyncio.run(d.start_stdin_reader(r, w))

            results = [r for r in http.split(w.getvalue())]

            # hello
            msg = to_rpc(results[0][1])
            self.assertTrue(isinstance(msg, JsonRPCResponse))
            self.assertEqual('hello world', msg.result)

            # add
            msg = to_rpc(results[1][1])
            self.assertTrue(isinstance(msg, JsonRPCResponse))
            self.assertEqual(3, msg.result)

    unittest.main()
