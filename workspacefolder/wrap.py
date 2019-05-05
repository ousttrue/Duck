import pathlib
import sys
import asyncio
import concurrent.futures
import subprocess
from typing import List

if sys.platform == "win32":
    # for asyncio.create_subprocess_exec
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


class Logger:
    def __init__(self, f, prefix):
        self.f = f
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
                        l=l[3:]
                    # add header
                    self.headers.append(l)
                    self.f.write(self.prefix)
                    self.f.write(l)
                    self.f.write(b'\n')
                    self.f.flush()

        else:
            #sys.stderr.write(f'body {len(self.buffer)}/{self.content_length}\n')
            # body
            if len(self.buffer) == self.content_length:
                self.f.write(self.prefix)
                self.f.write(self.buffer)
                self.f.write(b'\n')
                self.f.flush()
                self.buffer.clear()
                self.headers.clear()
                self.content_length = 0
                return True


async def stdin_to_childstdin(w: asyncio.StreamWriter, logger):
    loop = asyncio.get_event_loop()
    stdin = sys.stdin.buffer
    while True:
        b = await loop.run_in_executor(None, stdin.read, 1)
        if not b:
            logger.f.write(b'stdin break')
            break

        w.write(b)
        if logger.write(b):
            w.flush()


async def process_child_stdout(c: asyncio.StreamReader, logger):
    loop = asyncio.get_event_loop()
    while True:
        b = await loop.run_in_executor(None, c.read, 1)
        if not b:
            logger.f.write(b'stdout break\n')
            break

        # sync
        sys.stdout.buffer.write(b)
        if logger.write(b):
            sys.stdout.buffer.flush()


async def process_child_stderr(c: asyncio.StreamReader, log):
    while True:
        b = await loop.run_in_executor(None, c.readline)
        if not b:
            log.write(b'stderr break\n')
            break
        # sync
        sys.stderr.buffer.write(b)

        log.write(b'EE->')
        log.write(b)
        log.write('\n')
        log.flush()


async def launch(cmd: str, args: List[str], log):
    # create process
    p = subprocess.Popen(cmd,
                                             *args,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             stdin=subprocess.PIPE)

    asyncio.create_task(process_child_stderr(p.stderr, log))
    asyncio.create_task(stdin_to_childstdin(p.stdin, Logger(log, b'<--')))
    await process_child_stdout(p.stdout, Logger(log, b'-->'))

    #ret = await p.wait()
    #log.write(f'ret: {ret}\n'.encode('ascii'))
    #sys.exit(ret)


def execute(parsed):
    def run(log):
        cmd = parsed.args[0]
        args = parsed.args[1:]
        log.write(f'{cmd} {args}\n'.encode('utf-8'))
        asyncio.run(launch(cmd, args, log))

    if parsed.logfile:
        logfile = pathlib.Path(parsed.logfile)
        with logfile.open('wb') as log:
            run(log)
    else:
        run(sys.stderr.buffer)

