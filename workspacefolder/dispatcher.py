from typing import Dict, Any, Optional
import json

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

    def create_request(self, method, *args) -> bytes:
        request_id = self.next_request_id
        self.next_request_id += 1
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'id': request_id,
            'params': args,
        }
        json_request = json.dumps(request)
        return json_request.encode('utf-8')

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
            logger.error(message)

        else:
            raise ValueError()

        return None
