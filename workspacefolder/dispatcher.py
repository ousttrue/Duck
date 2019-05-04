import asyncio
import json
from typing import Dict, Any, Optional

import logging
from workspacefolder import json_rpc
logger = logging.getLogger(__name__)


def hello(target: str):
    return 'hello ' + target


def add(a, b):
    return a + b


RPC_KEY = '_RPC_METHOD'


def rpc_method(func, name: str = None):
    '''
    decorator for method marking
    '''

    setattr(func, RPC_KEY, name if name else func.__name__)
    return func


class Dispatcher:
    def __init__(self):
        self.method_map: Dict[str, Any] = {}
        self.next_request_id = 1
        self.request_map = {}

    def register(self, name: str, callback) -> None:
        self.method_map[name] = callback

    def register_dbug_methods(self) -> None:
        self.register('hello', hello)
        self.register('add', add)

    def register_methods(self, obj) -> None:
        for key in dir(obj):
            m = getattr(obj, key)
            if hasattr(m, RPC_KEY):
                name = getattr(m, RPC_KEY)
                if name:
                    self.register(name, m)

    def _create_request(self, method, *args):
        request_id = self.next_request_id
        self.next_request_id += 1
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': args,
            'id': request_id,
        }
        return request

    def async_request(self, w, method, *args) -> asyncio.Future:
        request = self._create_request(method, *args)

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.request_map[request['id']] = fut

        json_bytes = json.dumps(request).encode('utf-8')
        w.write(f'Content-Length: {len(json_bytes)}\r\n\r\n'.encode('ascii'))
        w.write(json_bytes)
        logger.debug('write: %s', json_bytes)

        return fut

    def dispatch_jsonrpc(self, body: bytes) -> Optional[bytes]:
        '''
        json_rpcメッセージを処理し、
            * メッセージがRequestだった場合
            * エラーメッセージがある場合
        結果を返す。
        '''
        #logger.debug(body)
        message = json_rpc.parse(body)
        #logger.debug(message)

        if isinstance(message, json_rpc.JsonRPCRequest):
            callback = self.method_map.get(message.method)
            if not callback:
                raise ValueError(f'{message.method} not found')

            if isinstance(message.params, dict):
                result = callback(**message.params)
                return json_rpc.to_bytes(message.id, result)

            elif isinstance(message.params, list):
                result = callback(*message.params)
                return json_rpc.to_bytes(message.id, result)

            else:
                raise ValueError('params not dict or list')

        elif isinstance(message, json_rpc.JsonRPCNotify):
            callback = self.method_map.get(message.method)
            if not callback:
                raise ValueError(f'{message.method} not found')

            if isinstance(message.params, dict):
                result = callback(**message.params)
                #return json_rpc.to_bytes(message.id, result)

            elif isinstance(message.params, list):
                result = callback(*message.params)
                #return json_rpc.to_bytes(message.id, result)

            else:
                raise ValueError('params not dict or list')

        elif isinstance(message, json_rpc.JsonRPCResponse):
            raise NotImplementedError()

        elif isinstance(message, json_rpc.JsonRPCError):
            self.dispatch_jsonerrror(message)

        else:
            raise ValueError()

        return None

    def dispatch_jsonerrror(self, err: json_rpc.JsonRPCError):
        if err.id:
            fut = self.request_map.get(err.id)
            if fut:
                fut.set_result(err)
                return
        logger.error(err)

