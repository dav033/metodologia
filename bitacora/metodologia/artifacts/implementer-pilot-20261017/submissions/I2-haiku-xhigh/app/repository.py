import copy
from bisect import bisect_right

from app.cursor import decode_cursor, encode_cursor

MIN_LIMIT = 1
MAX_LIMIT = 100


def _row_key(row):
    return (row['timestamp'], row['id'])


def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer')
    if not MIN_LIMIT <= limit <= MAX_LIMIT:
        raise ValueError(f'limit must be between {MIN_LIMIT} and {MAX_LIMIT}')


class Repository:
    def __init__(self, rows):
        self._rows = sorted((copy.deepcopy(row) for row in rows), key=_row_key)
        self._keys = [_row_key(row) for row in self._rows]

    def list_items(self, limit=20):
        return self.page(limit=limit)['items']

    def page(self, limit=20, cursor=None):
        _validate_limit(limit)
        start = 0 if cursor is None else bisect_right(self._keys, decode_cursor(cursor))
        end = start + limit
        items = copy.deepcopy(self._rows[start:end])
        next_cursor = None
        if end < len(self._rows):
            last = self._rows[end - 1]
            next_cursor = encode_cursor(last['timestamp'], last['id'])
        return {'items': items, 'next_cursor': next_cursor}
