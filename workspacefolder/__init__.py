import argparse

VERSION = [0, 1]


def main():
    parser = argparse.ArgumentParser(description='WorkspaceFolder tool.')

    sub = parser.add_subparsers(title='action')

    wrap = sub.add_parser('wrap')
    wrap.set_defaults(action='wrap')
    wrap.add_argument('cmd', type=str, nargs='+', help='''cmd and arguments''')

    args = parser.parse_args()

    if args.action == 'wrap':
        print(args.cmd)
    else:
        raise ValueError(args.action)


if __name__ == '__main__':
    main()
