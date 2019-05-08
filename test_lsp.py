import pathlib
import asyncio
import logging
from workspacefolder import lsp


if __name__ == '__main__':
    f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    lspi = lsp.LspInterface()

    async def run():
        path = pathlib.Path(__file__)
        text = path.read_text('utf-8')

        # ws = Workspace(path.parent, 'python')
        # await ws.async_initialized
        #
        # documen = Document(path, ws, text)

        await lspi.notify_document_open(path, text)

        # wait diagnostics
        await asyncio.sleep(2)

        await lspi.request_document_highlight(pathlib.Path(__file__), 0, 0)
        await lspi.request_document_definition(pathlib.Path(__file__), 0, 0)

        await lspi.notify_document_change(path, text)

        lspi.shutdown()
        logger.debug('done')

    asyncio.run(run())

