import argparse
import pathlib
import logging
from workspacefolder import rpc

# logging.lastResort = logging.NullHandler()
logger = logging.getLogger(__name__)

HERE = pathlib.Path(__file__).resolve().parent

VERSION = [0, 1]


def main():

    # parser setup
    parser = argparse.ArgumentParser(description='WorkspaceFolder tool.')
    parser.add_argument('--logfile', type=str, help='''cmd logfile''')
    parser.add_argument('--rpc',
                        action='store_true',
                        help='''enable rpc in stdinout''')
    parser.add_argument('--debug',
                        action='store_true',
                        help='''enable debug switch''')
    args = parser.parse_args()

    if args.debug:
        f = '%(asctime)s[%(levelname)s][%(name)s.%(funcName)s] %(message)s'
        logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S', format=f)
    else:
        # no output
        logging.lastResort = logging.NullHandler()

    #
    # start
    #
    if args.rpc:
        logger.debug('rpc')
        # start stdin reader
        rpc.execute(args)
    else:
        # execute tasks
        pass


if __name__ == '__main__':
    main()
