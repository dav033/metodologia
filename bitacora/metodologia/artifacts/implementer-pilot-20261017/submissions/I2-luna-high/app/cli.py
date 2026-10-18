import argparse
import json
import sys

from app.repository import Repository
from app.service import list_items


class _ParserExit(Exception):
    def __init__(self, status, message=""):
        super().__init__(message)
        self.status = status
        self.message = message


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ParserExit(2, f"{self.prog}: error: {message}\n")

    def exit(self, status=0, message=None):
        raise _ParserExit(status, message or "")


def main(argv=None, *, repo=None):
    parser = _ArgumentParser(prog="app.cli")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--cursor")
    try:
        args = parser.parse_args(argv)
        page = list_items(repo if repo is not None else Repository([]),
                          limit=args.limit, cursor=args.cursor)
        output = json.dumps(page)
    except _ParserExit as exc:
        stream = sys.stdout if exc.status == 0 else sys.stderr
        if exc.message:
            stream.write(exc.message)
        return exc.status
    except (ValueError, TypeError) as exc:
        message = str(exc).strip() or "invalid arguments"
        print(f"app.cli: error: {message}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
