import asyncio
import io
import logging
from typing import BinaryIO, List
if __name__ == '__main__':
    import http
else:
    from . import http
logger = logging.getLogger(__name__)


BOM = b'\xef\xbb\xbf'


class Dispatcher:
    def __init__(self):
        self.splitter = http.HttpSplitter()
        self.splitter.append_callback(self.on_http)

    def on_http(self, headers: List[bytes], body: bytes) -> None:
        logger.debug(body)

    async def start_stdin_reader(self, s: BinaryIO) -> None:
        loop = asyncio.get_event_loop()
        # stdin = sys.stdin.buffer
        bom_check = bytearray()
        while True:
            b: bytes = await loop.run_in_executor(None, s.read, 1)
            if not b:
                logger.debug('stdin break')
                break

            if bom_check is not None:
                # for powershell pipe
                bom_check.append(b[0])
                if len(bom_check) == 3:
                    if bytes(bom_check) != BOM:
                        for b in bom_check:
                            self.splitter.push(b)
                    bom_check = None

            else:
                self.splitter.push(b[0])


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

    s = io.BytesIO(BOM + b'Content-Length: 2\r\n\r\n{}')
    d = Dispatcher()
    asyncio.run(d.start_stdin_reader(s))

