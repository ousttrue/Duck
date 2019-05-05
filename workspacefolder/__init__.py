import logging
import sys
import argparse
import pathlib
from workspacefolder import rpc, wrap

# logging.lastResort = logging.NullHandler()
logger = logging.getLogger(__name__)

HERE = pathlib.Path(__file__).resolve().parent

VERSION = [0, 1]


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

    parser.add_argument('--wrap',
                        action='store_true')

    parser.add_argument('args', nargs='*')

    # parse
    parsed = parser.parse_args()

    # clear output
    #logging.lastResort = logging.NullHandler()
    level = logging.INFO
    if parsed.debug:
        level = logging.DEBUG

    if parsed.logfile:
        handler = logging.FileHandler(parsed.logfile)
    else:
        handler = logging.StreamHandler(sys.stderr.buffer)

    fmt = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
    f = logging.Formatter(fmt, '%H:%M:%S')
    handler.setLevel(level)
    handler.setFormatter(f)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)

    logging.info('############################################################')

    #
    # start
    #
    try:
        if parsed.rpc:
            # start stdin reader
            rpc.execute(parsed)
        elif parsed.wrap:
            # start command line launcher
            wrap.execute(parsed)
        else:
            # execute tasks
            pass

    finally:
        logging.shutdown()


if __name__ == '__main__':
    main()
