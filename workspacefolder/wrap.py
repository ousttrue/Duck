def setup_parser(parser) -> None:
    parser.add_argument('cmd',
                        type=str,
                        nargs='+',
                        help='''cmd and arguments''')


def execute(cmd):
    print(cmd)
