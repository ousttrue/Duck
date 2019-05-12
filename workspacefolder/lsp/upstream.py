import json
import logging
from typing import BinaryIO
from workspacefolder import util
from workspacefolder.rpc import json_rpc, dispatcher
logger = logging.getLogger(__name__)

PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
WINDOW_LOG = 'window/logMessage'


class UpstreamHandles:
    def __init__(self, f: BinaryIO) -> None:
        self.f = f

    @dispatcher.rpc_method_with_name(PUBLISH_DIAGNOSTICS)
    async def diagnostics(self, **kw):
        notify = json_rpc.JsonRPCNotify(PUBLISH_DIAGNOSTICS, kw)
        body = json.dumps(util.to_dict(notify))
        self.f.write(
            f'Content-Length: {len(body)}\r\n\r\n{body}'.encode('utf-8'))

    @dispatcher.rpc_method_with_name(WINDOW_LOG)
    async def log(self, **kw):
        #logger.debug('%s', kw)
        pass

