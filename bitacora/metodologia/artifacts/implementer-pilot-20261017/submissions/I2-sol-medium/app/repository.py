"""Snapshot storage with stable pagination by (timestamp, id)."""

import base64
import binascii
import copy
import json
import re
from bisect import bisect_right


def _validate_key(timestamp, id):
    if not isinstance(timestamp, int) or isinstance(timestamp, bool):
        raise ValueError('timestamp must be an integer')
    if not isinstance(id, str) or not id:
        raise ValueError('id must be a nonempty string')


def encode_cursor(timestamp, id):
    """Encode a pagination key as compact, unpadded URL-safe base64."""
    _validate_key(timestamp, id)
    data = json.dumps([timestamp, id], separators=(',', ':'), ensure_ascii=False)
    return base64.urlsafe_b64encode(data.encode('utf-8')).decode('ascii').rstrip('=')


def decode_cursor(cursor):
    """Decode and validate a cursor, reporting invalid input as ValueError."""
    if not isinstance(cursor, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', cursor):
        raise ValueError('cursor must be nonempty unpadded URL-safe base64')
    try:
        data = base64.b64decode(
            cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True
        )
        if base64.urlsafe_b64encode(data).decode('ascii').rstrip('=') != cursor:
            raise ValueError('invalid base64 cursor')
        key = json.loads(data.decode('utf-8'))
    except (binascii.Error, UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError('invalid cursor encoding or JSON') from exc
    if not isinstance(key, list) or len(key) != 2:
        raise ValueError('cursor must contain [timestamp,id]')
    _validate_key(*key)
    return tuple(key)


class Repository:
    def __init__(self, rows):
        self.rows = copy.deepcopy(list(rows))

    def list_items(self, limit=20):
        """Return the first page's items for legacy callers."""
        return self.page(limit=limit)['items']

    def page(self, limit=20, cursor=None):
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError('limit must be an integer from 1 to 100')
        after = decode_cursor(cursor) if cursor is not None else None
        rows = sorted(self.rows, key=lambda row: (row['timestamp'], row['id']))
        keys = [(row['timestamp'], row['id']) for row in rows]
        start = bisect_right(keys, after) if after is not None else 0
        end = start + limit
        items = copy.deepcopy(rows[start:end])
        next_cursor = encode_cursor(*keys[end - 1]) if end < len(rows) else None
        return {'items': items, 'next_cursor': next_cursor}
