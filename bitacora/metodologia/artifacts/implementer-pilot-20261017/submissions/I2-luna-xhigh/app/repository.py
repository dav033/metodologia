import base64
import copy
import json
import re


_URLSAFE_BASE64 = re.compile(r"[A-Za-z0-9_-]+\Z")


def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")


def encode_cursor(timestamp, id):
    """Encode a row's ordering tuple as an unpadded URL-safe cursor."""
    payload = json.dumps(
        [timestamp, id], separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(cursor):
    """Decode and validate a cursor's ``(timestamp, id)`` ordering tuple."""
    if not isinstance(cursor, str) or not cursor or not _URLSAFE_BASE64.fullmatch(cursor):
        raise ValueError("cursor must be unpadded URL-safe base64")

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = base64.b64decode(padded, altchars=b"-_", validate=True)
        # Reject non-canonical encodings, including encodings with non-zero pad bits.
        if base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=") != cursor:
            raise ValueError("malformed base64 cursor")
        decoded = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed cursor") from exc

    if not isinstance(decoded, list) or len(decoded) != 2:
        raise ValueError("cursor must contain a timestamp and id")
    timestamp, id = decoded
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise ValueError("cursor timestamp must be an integer")
    if not isinstance(id, str) or not id:
        raise ValueError("cursor id must be a nonempty string")
    return timestamp, id


class Repository:
    def __init__(self, rows):
        # Keep an isolated snapshot so later caller changes cannot alter pagination.
        self.rows = copy.deepcopy(list(rows))

    def page(self, limit=20, cursor=None):
        _validate_limit(limit)
        after = None if cursor is None else decode_cursor(cursor)

        ordered = sorted(self.rows, key=lambda row: (row["timestamp"], row["id"]))
        if after is not None:
            ordered = [
                row
                for row in ordered
                if (row["timestamp"], row["id"]) > after
            ]

        has_more = len(ordered) > limit
        selected = ordered[:limit]
        items = copy.deepcopy(selected)
        next_cursor = None
        if has_more:
            last = selected[-1]
            next_cursor = encode_cursor(last["timestamp"], last["id"])
        return {"items": items, "next_cursor": next_cursor}

    def list_items(self, limit=20):
        return self.page(limit=limit)["items"]
