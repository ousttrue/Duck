import sys
import argparse
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

VERSION = [0, 1]


def main():
    parser = argparse.ArgumentParser(description='WorkspaceFolder tool.')

    sub = parser.add_subparsers(title='action')

    wrap_parser = sub.add_parser('wrap')
    wrap_parser.set_defaults(action='wrap')
    if __name__ == '__main__':
        sys.path.append(str(HERE))
        import wrap
    else:
        # as module
        from . import wrap
    wrap.setup_parser(wrap_parser)

    args = parser.parse_args()

    if args.action == 'wrap':
        wrap.execute(args.cmd)
    else:
        raise ValueError(args.action)


if __name__ == '__main__':
    main()
