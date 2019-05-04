import json
from typing import NamedTuple, Union, Any
import logging
logger = logging.getLogger(__name__)


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


def parse(
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


def to_bytes(request_id: int, result: Any) -> bytes:
    value = {'jsonrpc': '2.0', 'id': request_id, 'result': result}
    value_str = json.dumps(value)
    utf = value_str.encode('utf-8')
    return utf
