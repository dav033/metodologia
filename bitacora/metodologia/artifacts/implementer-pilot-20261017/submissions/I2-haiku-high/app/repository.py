import base64
import binascii
import bisect
import copy
import json
import re

MIN_LIMIT = 1
MAX_LIMIT = 100
_CURSOR_PATTERN = re.compile(r'[A-Za-z0-9_-]+')


class Repository:
    """Read-only snapshot of rows, paginated in ascending (timestamp, id) order."""

    def __init__(self, rows):
        snapshot = copy.deepcopy(list(rows))
        self._rows = sorted(snapshot, key=_sort_key)
        self._keys = [_sort_key(row) for row in self._rows]

    def page(self, limit=20, cursor=None):
        _check_limit(limit)
        if cursor is None:
            start = 0
        else:
            # Strictly after the cursor tuple, whether or not a row with that tuple exists.
            start = bisect.bisect_right(self._keys, decode_cursor(cursor))
        end = start + limit
        items = [copy.deepcopy(row) for row in self._rows[start:end]]
        next_cursor = None
        if end < len(self._rows):
            last = self._rows[end - 1]
            next_cursor = encode_cursor(last['timestamp'], last['id'])
        return {'items': items, 'next_cursor': next_cursor}

    def list_items(self, limit=20):
        return self.page(limit=limit)['items']


def encode_cursor(timestamp, id):
    _check_timestamp(timestamp)
    _check_id(id)
    payload = json.dumps([timestamp, id], separators=(',', ':'), ensure_ascii=False)
    return _b64encode(payload.encode('utf-8'))


def decode_cursor(cursor):
    if not isinstance(cursor, str):
        raise ValueError('cursor must be a string')
    if not cursor:
        raise ValueError('cursor must not be empty')
    if _CURSOR_PATTERN.fullmatch(cursor) is None:
        raise ValueError('cursor must use only the URL-safe base64 alphabet without padding')
    raw = _b64decode(cursor)
    try:
        value = json.loads(raw.decode('utf-8'))
    except (ValueError, RecursionError) as exc:
        raise ValueError('cursor does not contain valid JSON') from exc
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('cursor must encode a [timestamp, id] pair')
    timestamp, id = value
    _check_timestamp(timestamp)
    _check_id(id)
    return timestamp, id


def _sort_key(row):
    return (row['timestamp'], row['id'])


def _check_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer')
    if not MIN_LIMIT <= limit <= MAX_LIMIT:
        raise ValueError(f'limit must be between {MIN_LIMIT} and {MAX_LIMIT}')


def _check_timestamp(timestamp):
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise ValueError('timestamp must be an integer')


def _check_id(id):
    if not isinstance(id, str) or not id:
        raise ValueError('id must be a nonempty string')


def _b64encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64decode(cursor):
    padded = cursor + '=' * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded)
    except binascii.Error as exc:
        raise ValueError('cursor is not valid base64') from exc
    # Reject non-canonical encodings (e.g. nonzero trailing bits) so only encode_cursor output is accepted.
    if _b64encode(raw) != cursor:
        raise ValueError('cursor is not valid base64')
    return raw
