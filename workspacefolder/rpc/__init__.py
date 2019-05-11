import logging
import asyncio
from . import dispatcher, stdinout
import workspacefolder.lsp
logger = logging.getLogger(__name__)


def setup_parser(parser):
    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')


def execute(parsed):
    logging.info('##################################################')

    d = dispatcher.Dispatcher(b'RPC')

    lspi = workspacefolder.lsp.LspInterface()
    d.register_methods(lspi)

    if parsed.debug:
        d.register_dbug_methods()

    # block until stdin break
    asyncio.run(stdinout.connect_with_dispatcher(d))
