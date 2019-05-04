from typing import Optional, List, Iterable, NamedTuple, Callable
import logging
logger = logging.getLogger(__name__)


def get_line(src: bytearray) -> Optional[bytes]:
    if len(src) >= 2:
        # CRLF
        if src[-2] == 13 and src[-1] == 10:
            return bytes(src[:-2])
    return None


class HttpRequest(NamedTuple):
    headers: List[bytes]
    body: bytes


class HttpSplitter:
    '''
    split keep-alive http stream to http messages
    '''

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.content_length = 0
        self.headers: List[bytes] = []

    def push(self, b: int) -> Optional[HttpRequest]:
        self.buffer.append(b)
        # logger.debug(self.buffer)
        if self.content_length == 0:
            # header
            line = get_line(self.buffer)
            if line is not None:  # may be empty
                self.buffer.clear()
                if len(line) == 0:
                    # found end of headers
                    # find Content-Length
                    for h in self.headers:
                        if h.startswith(b'Content-Length: '):
                            self.content_length = int(h[15:])
                            break
                else:
                    # add header
                    self.headers.append(line)

        else:
            # body
            if len(self.buffer) == self.content_length:
                body = bytes(self.buffer)

                request = HttpRequest(self.headers, body)

                self.buffer.clear()
                self.headers.clear()
                self.content_length = 0

                return request

        return None


def split(src: bytes) -> Iterable[HttpRequest]:
    logger.debug(src)
    splitter = HttpSplitter()

    for b in src:
        result = splitter.push(b)
        if result:
            yield result


# {{{
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

    import unittest

    class HttpSplitterTest(unittest.TestCase):
        def test_http_splitter(self):
            ht = HttpSplitter()

            http = [
                b'Content-Length: 2\r\n'
                b'\r\n',
                b'{}',
            ]

            for line in http:
                for b in line:
                    request = ht.push(b)

            self.assertTrue(request is not None)

    unittest.main()
# }}}
