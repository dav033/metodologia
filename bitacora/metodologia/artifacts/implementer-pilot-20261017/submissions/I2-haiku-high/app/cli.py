import argparse
import json
import re
import sys

from app.repository import Repository
from app.service import list_items

USAGE_ERROR = 2
_INTEGER_PATTERN = re.compile(r'[+-]?[0-9]+')


class _ParseExit(Exception):
    """Carries an argparse exit status and message back to main without raising SystemExit."""

    def __init__(self, status, message=None):
        super().__init__(status, message)
        self.status = status
        self.message = message


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ParseExit(USAGE_ERROR, f'{self.format_usage()}{self.prog}: error: {message}\n')

    def exit(self, status=0, message=None):
        raise _ParseExit(status, message)


def _integer(text):
    if _INTEGER_PATTERN.fullmatch(text) is None:
        raise argparse.ArgumentTypeError(f'invalid integer value: {text!r}')
    return int(text)


def _build_parser():
    parser = _Parser(prog='python -m app.cli', description='Print one page of items as JSON.')
    parser.add_argument('--limit', type=_integer, default=20, help='page size, 1..100 (default: 20)')
    parser.add_argument('--cursor', default=None, help='cursor from a previous page next_cursor')
    return parser


def main(argv=None, *, repo=None):
    try:
        args = _build_parser().parse_args(argv)
        page = list_items(
            repo if repo is not None else Repository([]),
            limit=args.limit,
            cursor=args.cursor,
        )
    except _ParseExit as exc:
        if exc.message:
            sys.stderr.write(exc.message)
        return exc.status
    except ValueError as exc:
        sys.stderr.write(f'error: {exc}\n')
        return USAGE_ERROR
    print(json.dumps(page))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
