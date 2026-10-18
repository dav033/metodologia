"""In-memory repository with stable tuple-based cursor pagination."""

import base64
import bisect
import copy
import json
import re


_CURSOR_ALPHABET = re.compile(r"[A-Za-z0-9_-]+\Z")


def encode_cursor(timestamp, id):
    """Encode a (timestamp, id) position as an unpadded URL-safe token."""
    payload = json.dumps([timestamp, id], separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor):
    """Decode and validate a pagination cursor."""
    if not isinstance(cursor, str) or not cursor or not _CURSOR_ALPHABET.fullmatch(cursor):
        raise ValueError("invalid cursor")
    try:
        raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != cursor:
            raise ValueError("non-canonical base64")
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid cursor") from exc
    if (not isinstance(value, list) or len(value) != 2
            or isinstance(value[0], bool) or not isinstance(value[0], int)
            or not isinstance(value[1], str) or not value[1]):
        raise ValueError("invalid cursor")
    return value[0], value[1]


def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")


class Repository:
    def __init__(self, rows):
        # Rows and nested JSON payloads are snapshotted at construction.
        self.rows = copy.deepcopy(list(rows))

    def page(self, limit=20, cursor=None):
        _validate_limit(limit)
        position = decode_cursor(cursor) if cursor is not None else None
        ordered = sorted(self.rows, key=lambda row: (row["timestamp"], row["id"]))
        keys = [(row["timestamp"], row["id"]) for row in ordered]
        start = bisect.bisect_right(keys, position) if position is not None else 0
        selected = ordered[start:start + limit]
        has_more = start + len(selected) < len(ordered)
        next_cursor = encode_cursor(*keys[start + len(selected) - 1]) if has_more else None
        return {"items": copy.deepcopy(selected), "next_cursor": next_cursor}

    def list_items(self, limit=20):
        return self.page(limit=limit)["items"]
