import unittest
import asyncio
import logging
import pathlib
from workspacefolder import lsp
logger = logging.getLogger(__name__)


class LspTests(unittest.TestCase):
    def test_pyls(self):
        async def run():
            path = pathlib.Path(__file__)
            text = path.read_text('utf-8')

            lspi = lsp.LspInterface()

            document = lspi.get_or_create_document(path)

            await document.notify_open(text)

            # wait diagnostics
            await asyncio.sleep(1)

            await document.notify_change(text)

            await document.request_highlight(0, 0)
            await document.request_definition(0, 0)
            await document.request_completion(44-1, 16-1)
            await document.request_hover(0, 0)
            await document.request_references(0, 0)

            await asyncio.sleep(2)

            lspi.shutdown()
            logger.debug('done')

        asyncio.run(run())


if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)

    unittest.main()
