import pathlib
import sys
import asyncio
import concurrent.futures
import subprocess
import logging
from typing import List
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


class Splitter:
    def __init__(self, prefix):
        self.content_length = 0
        self.headers = []
        self.buffer = bytearray()
        self.prefix = prefix

    def write(self, b):
        self.buffer += b
        if self.content_length == 0:
            # header
            if len(self.buffer
                   ) >= 2 and self.buffer[-2] == 13 and self.buffer[-1] == 10:
                # found eol
                l = bytes(self.buffer[:-2])
                self.buffer.clear()
                if len(l) == 0:
                    # found end of headers
                    # find Content-Length
                    for h in self.headers:
                        if h.startswith(b'Content-Length: '):
                            self.content_length = int(h[15:])
                            break
                else:
                    if l[0:3] == b'\xEF\xBB\xBF':
                        l = l[3:]
                    # add header
                    self.headers.append(l)
                    logger.debug(self.prefix)
                    logger.debug(l)
                    logger.debug(b'\n')

        else:
            #sys.stderr.write(f'body {len(self.buffer)}/{self.content_length}\n')
            # body
            if len(self.buffer) == self.content_length:
                logger.debug(self.prefix)
                logger.debug(self.buffer)
                logger.debug(b'\n')
                self.buffer.clear()
                self.headers.clear()
                self.content_length = 0
                return True


async def stdin_to_childstdin(w: asyncio.StreamWriter, splitter):
    loop = asyncio.get_event_loop()
    stdin = sys.stdin.buffer
    while True:
        b = await loop.run_in_executor(None, stdin.read, 1)
        if not b:
            logger.debug(b'stdin break')
            break

        w.write(b)
        if splitter.write(b):
            w.flush()


async def process_child_stdout(c: asyncio.StreamReader, splitter):
    loop = asyncio.get_event_loop()
    while True:
        b = await loop.run_in_executor(None, c.read, 1)
        if not b:
            logger.debug(b'stdout break\n')
            break

        # sync
        sys.stdout.buffer.write(b)
        if splitter.write(b):
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

        logger.debug(b'EE->')
        logger.debug(b)
        logger.debug('\n')


async def launch(cmd: str, args: List[str]):
    # create process
    p = subprocess.Popen(cmd,
                         *args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)

    asyncio.create_task(process_child_stderr(p.stderr))
    asyncio.create_task(stdin_to_childstdin(p.stdin, Splitter(b'<--')))
    await process_child_stdout(p.stdout, Splitter(b'-->'))

    #ret = await p.wait()
    #log.write(f'ret: {ret}\n'.encode('ascii'))
    #sys.exit(ret)


def execute(parsed):
    cmd = parsed.args[0]
    args = parsed.args[1:]
    logger.debug(f'{cmd} {args}\n'.encode('utf-8'))
    asyncio.run(launch(cmd, args))
