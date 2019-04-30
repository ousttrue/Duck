import sys
import argparse
import pathlib
import asyncio
import logging
from . import rpc

# logging.lastResort = logging.NullHandler()
logger = logging.getLogger(__name__)

HERE = pathlib.Path(__file__).resolve().parent

VERSION = [0, 1]


def main():
    # setup logger
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s')

    # parser setup
    parser = argparse.ArgumentParser(description='WorkspaceFolder tool.')
    parser.add_argument('--logfile', type=str, help='''cmd logfile''')
    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')
    args = parser.parse_args()

    #
    # start
    #
    if args.rpc:
        logger.debug('rpc')
        # start stdin reader
        dispatcher = rpc.Dispatcher()

        # block until stdin break
        asyncio.run(dispatcher.start_stdin_reader(sys.stdin.buffer))

    else:
        # execute tasks
        pass


if __name__ == '__main__':
    main()
