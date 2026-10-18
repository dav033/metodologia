"""In-memory repository with stable cursor pagination ordered by (timestamp, id)."""
import bisect
import copy

from app.cursor import decode_cursor, encode_cursor

DEFAULT_LIMIT = 20
MIN_LIMIT = 1
MAX_LIMIT = 100

__all__ = [
    'DEFAULT_LIMIT',
    'MAX_LIMIT',
    'MIN_LIMIT',
    'Repository',
    'decode_cursor',
    'encode_cursor',
]


def _sort_key(row):
    return (row['timestamp'], row['id'])


def _validate_limit(limit):
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError('limit must be an integer')
    if not MIN_LIMIT <= limit <= MAX_LIMIT:
        raise ValueError(f'limit must be between {MIN_LIMIT} and {MAX_LIMIT}')


class Repository:
    def __init__(self, rows):
        # Deep copies keep caller-owned rows isolated from this repository.
        snapshot = sorted((copy.deepcopy(row) for row in rows), key=_sort_key)
        self._rows = snapshot
        self._keys = [_sort_key(row) for row in snapshot]

    def page(self, limit=DEFAULT_LIMIT, cursor=None):
        _validate_limit(limit)
        start = 0
        if cursor is not None:
            # Rows strictly after the cursor tuple; the cursor's row need not exist.
            start = bisect.bisect_right(self._keys, decode_cursor(cursor))
        end = start + limit
        items = [copy.deepcopy(row) for row in self._rows[start:end]]
        next_cursor = None
        if end < len(self._rows):
            next_cursor = encode_cursor(*self._keys[end - 1])
        return {'items': items, 'next_cursor': next_cursor}

    def list_items(self, limit=DEFAULT_LIMIT):
        return self.page(limit=limit)['items']
