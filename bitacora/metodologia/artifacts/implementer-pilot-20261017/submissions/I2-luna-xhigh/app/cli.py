import argparse
import json
import sys

from app.repository import Repository
from app.service import list_items


class _ArgumentError(Exception):
    pass


class _ArgumentExit(Exception):
    def __init__(self, status):
        self.status = status


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentError(message)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stdout if status == 0 else sys.stderr)
        raise _ArgumentExit(status)


def main(argv=None, *, repo=None):
    parser = _ArgumentParser(
        description="List items with cursor pagination.", allow_abbrev=False
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--cursor")

    try:
        args = parser.parse_args(argv)
        page = list_items(
            repo if repo is not None else Repository([]),
            limit=args.limit,
            cursor=args.cursor,
        )
    except (_ArgumentError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except _ArgumentExit as exc:
        return exc.status

    print(json.dumps(page))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
