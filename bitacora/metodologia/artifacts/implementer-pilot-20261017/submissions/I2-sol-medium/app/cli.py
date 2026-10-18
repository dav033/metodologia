"""Command-line interface for paginated item listings."""

import argparse
import json
import re
import sys

from app.repository import Repository
from app.service import list_items


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _integer(value):
    if not re.fullmatch(r'[+-]?[0-9]+', value):
        raise ValueError('limit must be an integer')
    return int(value)


def main(argv=None, *, repo=None):
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument('--limit', type=_integer, default=20)
    parser.add_argument('--cursor')
    try:
        args = parser.parse_args(argv)
        page = list_items(
            repo if repo is not None else Repository([]),
            limit=args.limit,
            cursor=args.cursor,
        )
        output = json.dumps(page)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
