"""Command-line entry point printing one JSON page of items."""
import argparse
import json
import sys

from app.repository import DEFAULT_LIMIT, MAX_LIMIT, MIN_LIMIT, Repository
from app.service import list_items

USAGE_ERROR = 2


class _ArgumentError(Exception):
    """Raised instead of argparse exiting, so main can return a status code."""

    def __init__(self, status, text):
        super().__init__(text)
        self.status = status
        self.text = text


class _NonExitingParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentError(USAGE_ERROR, f'{self.format_usage()}{self.prog}: error: {message}')

    def exit(self, status=0, message=None):
        raise _ArgumentError(status, message or '')


def _build_parser():
    parser = _NonExitingParser(prog='python -m app.cli')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT,
                        help=f'page size, {MIN_LIMIT}..{MAX_LIMIT} (default: {DEFAULT_LIMIT})')
    parser.add_argument('--cursor', default=None,
                        help='opaque cursor from a previous page')
    return parser


def _fail(status, text):
    if text:
        print(text.rstrip(), file=sys.stderr)
    return status


def main(argv=None, *, repo=None):
    try:
        args = _build_parser().parse_args(argv)
    except _ArgumentError as exc:
        return _fail(exc.status, exc.text)
    if repo is None:
        repo = Repository([])
    try:
        page = list_items(repo, limit=args.limit, cursor=args.cursor)
    except ValueError as exc:
        return _fail(USAGE_ERROR, f'error: {exc}')
    print(json.dumps(page))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
