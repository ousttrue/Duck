import sys
import asyncio
import logging
from typing import List, BinaryIO
from workspacefolder import http, pipestream, util
logger = logging.getLogger(__name__)


async def process_stdin(r: BinaryIO, w: BinaryIO) -> None:
    splitter = http.HttpSplitter()
    loop = asyncio.get_event_loop()
    while True:
        b = await loop.run_in_executor(None, r.read, 1)
        if not b:
            logger.debug(b'stdin break')
            break

        w.write(b)
        request = splitter.push(b[0])
        if request:
            # logging
            body = util.indent_json(request.body)
            logger.debug('<--' + body)

            w.flush()


def write_http(w: BinaryIO, body: bytes) -> None:
    w.write(f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii'))
    w.write(body)
    w.flush()


def on_out(request: http.HttpRequest) -> None:
    # logging
    body = util.indent_json(request.body)
    logger.debug('-->' + body)
    # through
    write_http(sys.stdout.buffer, request.body)


def on_error(line: bytes) -> None:
    logger.error(b'EE->' + line + b'\n')


async def launch(cmd: str, args: List[str]):
    ps = pipestream.PipeStream(cmd, *args)

    asyncio.create_task(ps.process_stdout(on_out))
    asyncio.create_task(ps.process_stderr(on_error))
    await process_stdin(sys.stdin.buffer, ps.p.stdin)


def setup_parser(parser):
    parser.add_argument('--wrap', action='store_true')


def execute(parsed):
    cmd = parsed.args[0]
    args = parsed.args[1:]
    asyncio.run(launch(cmd, args))
