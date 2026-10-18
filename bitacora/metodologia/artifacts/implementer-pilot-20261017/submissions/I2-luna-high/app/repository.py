import base64
import binascii
import copy
import json
import re


_CURSOR_ALPHABET = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")


def _validate_cursor_values(timestamp, item_id):
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise ValueError("timestamp must be an integer")
    if not isinstance(item_id, str) or not item_id:
        raise ValueError("id must be a nonempty string")


class Repository:
    def __init__(self, rows):
        # Copy the full payload tree so callers cannot mutate the repository
        # through either the original input or a returned page.
        self.rows = copy.deepcopy(list(rows))

    def list_items(self, limit=20):
        return self.page(limit=limit)["items"]

    def page(self, limit=20, cursor=None):
        _validate_limit(limit)
        after = None if cursor is None else decode_cursor(cursor)

        ordered = sorted(self.rows, key=lambda row: (row["timestamp"], row["id"]))
        if after is not None:
            ordered = [row for row in ordered if (row["timestamp"], row["id"]) > after]

        has_more = len(ordered) > limit
        selected = ordered[:limit]
        items = copy.deepcopy(selected)
        next_cursor = None
        if has_more:
            last = selected[-1]
            next_cursor = encode_cursor(last["timestamp"], last["id"])
        return {"items": items, "next_cursor": next_cursor}


def encode_cursor(timestamp, id):
    _validate_cursor_values(timestamp, id)
    payload = json.dumps([timestamp, id], separators=(",", ":"), ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def decode_cursor(cursor):
    if not isinstance(cursor, str) or not cursor or not _CURSOR_ALPHABET.fullmatch(cursor):
        raise ValueError("cursor must be unpadded URL-safe base64")
    if len(cursor) % 4 == 1:
        raise ValueError("malformed cursor base64")
    try:
        padded = cursor + "=" * ((-len(cursor)) % 4)
        raw = base64.b64decode(padded, altchars=b"-_", validate=True)
        # Require a canonical token, including valid unused bits in the final
        # base64 character.
        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != cursor:
            raise ValueError("malformed cursor base64")
        value = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed cursor") from exc

    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("cursor must contain a timestamp and id")
    timestamp, item_id = value
    _validate_cursor_values(timestamp, item_id)
    return timestamp, item_id
