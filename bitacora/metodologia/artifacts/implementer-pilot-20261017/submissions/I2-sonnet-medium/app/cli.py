import argparse
import json
import sys

from app.repository import Repository
from app.service import list_items


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgError(message)


def _build_parser():
    parser = _Parser(prog='app.cli', add_help=False, allow_abbrev=False)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--cursor', default=None)
    return parser


def main(argv=None, *, repo=None):
    try:
        args = _build_parser().parse_args(argv)
        page = list_items(repo if repo is not None else Repository([]),
                          limit=args.limit, cursor=args.cursor)
        output = json.dumps(page)
    except (_ArgError, ValueError) as exc:
        print('error: %s' % (exc or 'invalid input'), file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
