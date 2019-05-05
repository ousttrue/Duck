import asyncio
import json
from typing import Dict, Any, Optional, Union

import logging
from workspacefolder import json_rpc
logger = logging.getLogger(__name__)


async def hello(target: str):
    return 'hello ' + target


async def add(a, b):
    return a + b


RPC_KEY = '_RPC_METHOD'


def rpc_method(func, name: str = None):
    '''
    decorator for method marking
    '''

    setattr(func, RPC_KEY, name if name else func.__name__)
    return func


class Dispatcher:
    def __init__(self, name: str) -> None:
        self.name = name
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

    def create_request(self, method, *args, **kw) -> json_rpc.JsonRPCRequest:
        params: Any = None
        if args and kw:
            raise ValueError()
        elif args:
            params = args
        elif kw:
            params = kw

        request_id = self.next_request_id
        self.next_request_id += 1

        request = json_rpc.JsonRPCRequest(method, params, request_id)

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.request_map[request.id] = fut

        return request

    async def wait_request(
            self, request: json_rpc.JsonRPCRequest
    ) -> Union[json_rpc.JsonRPCResponse, json_rpc.JsonRPCError]:

        fut = self.request_map[request.id]
        return await fut

    async def async_dispatch(self, body: bytes) -> Optional[bytes]:
        '''
        json_rpcメッセージを処理し、
            * メッセージがRequestだった場合
            * エラーメッセージがある場合
        結果を返す。
        '''
        message = json_rpc.parse(body)

        if isinstance(message, json_rpc.JsonRPCRequest):
            callback = self.method_map.get(message.method)
            if not callback:
                logger.error('%s: %s not found', self.name, message.method)

            if isinstance(message.params, dict):
                result = await callback(**message.params)
                return json_rpc.to_bytes(message.id, result)

            elif isinstance(message.params, list):
                result = await callback(*message.params)
                return json_rpc.to_bytes(message.id, result)

            else:
                logger.error('%s: params not dict or list', self.name)

        elif isinstance(message, json_rpc.JsonRPCNotify):
            callback = self.method_map.get(message.method)
            if not callback:
                logger.error('%s: %s not found', self.name, message.method)

            if isinstance(message.params, dict):
                await callback(**message.params)

            elif isinstance(message.params, list):
                await callback(*message.params)

            else:
                logger.error('%s: params not dict or list', self.name)

        elif isinstance(message, json_rpc.JsonRPCResponse):
            self.dispatch_response(message)

        elif isinstance(message, json_rpc.JsonRPCError):
            self.dispatch_errror(message)

        else:
            logger.error('%s: invalid message: %s', self.name, message)

        return None

    def dispatch_response(self, res: json_rpc.JsonRPCResponse):
        request_id = res.id
        if request_id:
            fut = self.request_map.get(request_id)
            if fut:
                fut.set_result(res.result)
                return
        logger.error('%s: %s', self.name, res)

    def dispatch_errror(self, err: json_rpc.JsonRPCError):
        request_id = err.id
        if request_id:
            fut = self.request_map.get(request_id)
            if fut:
                fut.set_result(err.error)
                return
        logger.error('%s: %s', self.name, err)
