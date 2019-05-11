import logging
import pathlib
import asyncio
from typing import Any
from . import dispatcher, stdinout
import workspacefolder.lsp
logger = logging.getLogger(__name__)

REQUEST_PREFIX = 'request_'
NOTIFY_PREFIX = 'notify_'

def register(lspi, d, key, register_name):
    async def callback(_path: str, *args, **kw)->Any:
        path = pathlib.Path(_path)
        doc = lspi.get_or_create_document(path)
        if doc:
            method = getattr(doc, key)
            return await method(*args)
    d.register(register_name, callback)


def register_lsp(d: dispatcher.Dispatcher, lspi: workspacefolder.lsp.LspInterface)->None:
    for key in dir(workspacefolder.lsp.document.Document):
        register_name = None
        if key.startswith(REQUEST_PREFIX):
            register_name = 'request_document_' + key[len(REQUEST_PREFIX):]
        elif key.startswith(NOTIFY_PREFIX):
            register_name = 'notify_document_' + key[len(NOTIFY_PREFIX):]
        else:
            continue

        register(lspi, d, key, register_name)


def setup_parser(parser):
    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')


def execute(parsed):
    logging.info('##################################################')

    d = dispatcher.Dispatcher(b'RPC')

    lspi = workspacefolder.lsp.LspInterface()
    register_lsp(d, lspi)

    if parsed.debug:
        d.register_dbug_methods()

    # block until stdin break
    asyncio.run(stdinout.connect_with_dispatcher(d))
