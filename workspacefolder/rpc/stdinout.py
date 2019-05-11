import asyncio
import sys
import json
import io
import logging
from typing import BinaryIO
from . import http, dispatcher
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


async def stdin_dispatch_stdout(r: BinaryIO, w: BinaryIO,
                       dispatcher: dispatcher.Dispatcher) -> None:
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


async def connect_with_dispatcher(d: dispatcher.Dispatcher) -> None:
    await stdin_dispatch_stdout(sys.stdin.buffer, sys.stdout.buffer, d)
