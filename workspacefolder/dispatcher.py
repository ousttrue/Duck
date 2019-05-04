from typing import Dict, Any, Optional

import logging
from workspacefolder import json_rpc
logger = logging.getLogger(__name__)


def hello(target: str):
    return 'hello ' + target


def add(a, b):
    return a + b



class Dispatcher:
    def __init__(self):
        self.method_map: Dict[str, Any] = {}

    def register(self, name: str, callback) -> None:
        self.method_map[name] = callback

    def register_dbug_methods(self) -> None:
        self.register('hello', hello)
        self.register('add', add)

    def dispatch_jsonrpc(self, body: bytes) -> Optional[bytes]:
        '''
        json_rpcメッセージを処理し、
            * メッセージがRequestだった場合
            * エラーメッセージがある場合
        結果を返す。
        '''
        logger.debug(body)
        message = json_rpc.parse(body)
        logger.debug(message)

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
            raise NotImplementedError()

        elif isinstance(message, json_rpc.JsonRPCResponse):
            raise NotImplementedError()

        elif isinstance(message, json_rpc.JsonRPCError):
            raise NotImplementedError()

        else:
            raise ValueError()
