import pathlib
import sys
import os
import asyncio
import concurrent.futures
import subprocess
from typing import List

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


async def stdin_to_childstdin(w: asyncio.StreamWriter, pool, logger):
    loop = asyncio.get_event_loop()
    stdin = sys.stdin.buffer
    buf = bytearray()
    while True:
        b = await loop.run_in_executor(
                pool, stdin.read, 1)
        if not b:
            logger(b'stdin break')
            break
        w.write(b)

        if b==b'\n':
            logger(b'<--'+bytes(buf))
            buf.clear()
        else:
            buf+=b


async def process_child_stdout(c: asyncio.StreamReader, logger):
    buf = bytearray()
    while True:
        b = await c.read(1)
        if not b:
            logger(b'stdout break')
            break
        # sync
        sys.stdout.buffer.write(b)

        if b==b'\n':
            logger(b'-->'+bytes(buf))
            buf.clear()
        else:
            buf+=b

async def process_child_stderr(c: asyncio.StreamReader, logger):
    buf = bytearray()
    while True:
        b = await c.read(1)
        if not b:
            logger(b'stderr break')
            break
        # sync
        #sys.stdout.buffer.write(b)

        if b==b'\n':
            logger(b'EE>'+bytes(buf))
            buf.clear()
        else:
            buf+=b


async def launch(cmd: str, args: List[str], logger):
    # create process
    p = await asyncio.create_subprocess_exec(cmd,
                                             *args,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             stdin=subprocess.PIPE)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        asyncio.create_task(process_child_stderr(p.stderr, logger))
        asyncio.create_task(process_child_stdout(p.stdout, logger))
        asyncio.create_task(stdin_to_childstdin(p.stdin, pool, logger))

        ret = await p.wait()
        logger(f'ret: {ret}\n'.encode('ascii'))
        sys.exit(ret)


def setup_parser(parser) -> None:
    parser.add_argument('--logfile', type=str, help='''cmd logfile''')
    parser.add_argument('cmd', type=str, help='''cmd''')
    parser.add_argument('args', type=str, nargs='*', help='''cmd arguments''')


def execute(parsed):
    logfile = pathlib.Path(parsed.logfile)

    with logfile.open('wb') as log:
        def logger(*args):
            for arg in args:
                log.write(arg)
            log.write(b'\n')
            log.flush()


        logger(f'{parsed.cmd} {parsed.args}\n'.encode('utf-8'))
        asyncio.run(launch(parsed.cmd, parsed.args, logger))
