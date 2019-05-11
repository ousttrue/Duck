import unittest
import asyncio
import json
import io
from workspacefolder import rpc
from workspacefolder.rpc import http, json_rpc, dispatcher, stdinout
import logging
logger = logging.getLogger(__name__)


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
        return f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii') + body

    def test_Rpc(self):
        r = io.BytesIO()
        r.write(stdinout.BOM)
        r.write(self.create_request('hello', 'world'))
        r.write(self.create_request('add', 1, 2))
        r.seek(0, 0)

        w = io.BytesIO()
        d = dispatcher.Dispatcher('RPCTest')

        d.register_dbug_methods()

        asyncio.run(stdinout.stdin_dispatch_stdout(r, w, d))

        results = [r for r in http.split(w.getvalue())]

        # hello
        body = results[0].body.decode('utf-8')
        msg = json_rpc.parse(json.loads(body))
        self.assertTrue(isinstance(msg, json_rpc.JsonRPCResponse))
        self.assertEqual('hello world', msg.result)

        # add
        body = results[1].body.decode('utf-8')
        msg = json_rpc.parse(json.loads(body))
        self.assertTrue(isinstance(msg, json_rpc.JsonRPCResponse))
        self.assertEqual(3, msg.result)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

    unittest.main()
