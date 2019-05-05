import pathlib
import sys
import asyncio
import concurrent.futures
import subprocess
import logging
from typing import List
from workspacefolder import http
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


async def stdin_to_childstdin(w: asyncio.StreamWriter,
                              splitter: http.HttpSplitter):
    loop = asyncio.get_event_loop()
    stdin = sys.stdin.buffer
    while True:
        b = await loop.run_in_executor(None, stdin.read, 1)
        if not b:
            logger.debug(b'stdin break')
            break

        w.write(b)
        request = splitter.push(b[0])
        if request:
            logger.debug(b'<--' + request.body)
            w.flush()


async def process_child_stdout(c: asyncio.StreamReader,
                               splitter: http.HttpSplitter):
    loop = asyncio.get_event_loop()
    while True:
        b = await loop.run_in_executor(None, c.read, 1)
        if not b:
            logger.debug(b'stdout break\n')
            break

        # sync
        sys.stdout.buffer.write(b)
        request = splitter.push(b[0])
        if request:
            logger.debug(b'-->' + request.body)
            sys.stdout.buffer.flush()


async def process_child_stderr(c: asyncio.StreamReader):
    loop = asyncio.get_event_loop()
    while True:
        b = await loop.run_in_executor(None, c.readline)
        if not b:
            log.write(b'stderr break\n')
            break
        # sync
        sys.stderr.buffer.write(b)

        logger.debug(b'EE->' + b + b'\n')


async def launch(cmd: str, args: List[str]):
    p = subprocess.Popen(cmd,
                         *args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)

    asyncio.create_task(process_child_stderr(p.stderr))
    asyncio.create_task(stdin_to_childstdin(p.stdin, http.HttpSplitter()))
    await process_child_stdout(p.stdout, http.HttpSplitter())


def execute(parsed):
    cmd = parsed.args[0]
    args = parsed.args[1:]
    logger.debug(f'{cmd} {args}\n'.encode('utf-8'))
    asyncio.run(launch(cmd, args))
