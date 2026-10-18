import json
import argparse
import sys
from app.repository import Repository
from app.service import list_items


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None, *, repo=None):
    parser = _Parser(prog="app.cli")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--cursor", default=None)
    try:
        args = parser.parse_args(argv)
        page = list_items(repo if repo is not None else Repository([]),
                          limit=args.limit, cursor=args.cursor)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(page, ensure_ascii=False))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
