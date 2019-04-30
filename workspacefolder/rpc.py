import sys
import asyncio
import logging
logger = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self):
        pass

    def stdin_on_read(self, b) -> None:
        logger.debug(b)

    async def start_stdin_reader(self):
        loop = asyncio.get_event_loop()
        stdin = sys.stdin.buffer
        while True:
            b = await loop.run_in_executor(None, stdin.read, 1)
            if not b:
                logger.debug('stdin break')
                break

            self.stdin_on_read(b)
