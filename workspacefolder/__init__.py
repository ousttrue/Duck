import logging
import sys
import argparse
import pathlib
from . import rpc, wrap, task

logger = logging.getLogger(__name__)

VERSION = [0, 1]

if sys.platform == "win32":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def setup_logger(debug: bool, logfile: str) -> None:
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    else:
        # clear output
        logging.lastResort = logging.NullHandler()

    if logfile:
        handler = logging.FileHandler(logfile, encoding='utf-8')
    else:
        handler = logging.StreamHandler(sys.stderr)

    fmt = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    f = logging.Formatter(fmt, '%H:%M:%S')
    handler.setLevel(level)
    handler.setFormatter(f)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)


def main():

    # parser setup
    parser = argparse.ArgumentParser(description='WorkspaceFolder tool.')
    parser.add_argument('--logfile', type=str, help='''cmd logfile''')
    parser.add_argument('--debug',
                        action='store_true',
                        help='''enable debug switch''')

    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')

    parser.add_argument('--wrap', action='store_true')

    parser.add_argument('args', nargs='*')

    # parse
    parsed = parser.parse_args()

    setup_logger(parsed.debug, parsed.logfile)

    # start
    try:
        if parsed.rpc:
            # start stdin reader
            rpc.execute(parsed)
        elif parsed.wrap:
            # start command line launcher
            wrap.execute(parsed)
        else:
            # execute tasks
            if not task.execute(parsed):
                parser.print_help()

    finally:
        logging.shutdown()

