import argparse
import json
import sys

from app.repository import Repository
from app.service import list_items


class _ParseExit(Exception):
    def __init__(self, status, message=None):
        super().__init__(status, message)
        self.status = status
        self.message = message


class _ArgumentParser(argparse.ArgumentParser):
    # Report parse failures through main()'s return code instead of SystemExit.
    def error(self, message):
        raise _ParseExit(2, f'{self.format_usage().rstrip()}\n{self.prog}: error: {message}')

    def exit(self, status=0, message=None):
        raise _ParseExit(status, message)


def _build_parser():
    parser = _ArgumentParser(prog='python -m app.cli', description='Print one page of items as JSON.')
    parser.add_argument('--limit', type=int, default=20, help='items per page, 1-100 (default: 20)')
    parser.add_argument('--cursor', default=None, help='next_cursor from a previous page')
    return parser


def main(argv=None, *, repo=None):
    try:
        args = _build_parser().parse_args(argv)
    except _ParseExit as exc:
        if exc.message:
            print(exc.message.rstrip('\n'), file=sys.stderr)
        return exc.status
    if repo is None:
        repo = Repository([])
    try:
        page = list_items(repo, limit=args.limit, cursor=args.cursor)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(page))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
