import unittest
import asyncio
import logging
import pathlib
from workspacefolder import lsp
logger = logging.getLogger(__name__)


class LspTests(unittest.TestCase):
    def test_run(self):
        async def run():
            path = pathlib.Path(__file__)
            text = path.read_text('utf-8')

            lspi = lsp.LspInterface()

            # ws = Workspace(path.parent, 'python')
            # await ws.async_initialized
            #
            # documen = Document(path, ws, text)

            await lspi.notify_document_open(path, text)

            # wait diagnostics
            await asyncio.sleep(1)

            await lspi.notify_document_change(path, text)

            await lspi.request_document_highlight(pathlib.Path(__file__), 0, 0)
            await lspi.request_document_definition(pathlib.Path(__file__), 0,
                                                   0)

            await asyncio.sleep(2)

            lspi.shutdown()
            logger.debug('done')

        asyncio.run(run())


if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)

    unittest.main()
