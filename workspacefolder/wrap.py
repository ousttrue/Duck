import sys
import asyncio
import subprocess
from typing import List

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


class Win32StdinReader:
    def __init__(self):
        self.stdin = sys.stdin.buffer
        self.loop = asyncio.get_event_loop()

    async def readline(self):
        return await self.loop.run_in_executor(None, self.stdin.readline)

    async def read(self, n):
        return await self.loop.run_in_executor(
            None, lambda: self.stdin.read(n))


async def stdin_to_childstdin(w: asyncio.StreamWriter):
    if sys.platform == "win32":
        r = Win32StdinReader()
    else:
        r = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(r)
        await loop.connect_read_pipe(lambda: protocol,
                                     sys.stdin)  # sets read_transport

    while True:
        b = await r.readline()
        if not b:
            break
        w.write(b)


async def childstdout_to_stdout(c: asyncio.StreamReader):
    while True:
        b = await c.read(1)
        if not b:
            break
        # sync
        sys.stdout.buffer.write(b)


async def launch(cmd: str, args: List[str]):
    # create process
    p = await asyncio.create_subprocess_exec(cmd,
                                             *args,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             stdin=subprocess.PIPE)
    asyncio.create_task(stdin_to_childstdin(p.stdin))
    asyncio.create_task(childstdout_to_stdout(p.stderr))
    asyncio.create_task(childstdout_to_stdout(p.stdout))
    ret = await p.wait()
    print(ret)
    sys.exit(ret)


def setup_parser(parser) -> None:
    parser.add_argument('cmd', type=str, help='''cmd''')
    parser.add_argument('args', type=str, nargs='*', help='''cmd arguments''')


def execute(parsed):
    asyncio.run(launch(parsed.cmd, parsed.args))
