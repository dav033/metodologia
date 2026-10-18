import base64
import binascii
import copy
import json
import re

_CURSOR_RE = re.compile(r'[A-Za-z0-9_-]+')


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def encode_cursor(timestamp, id):
    if not _is_int(timestamp):
        raise ValueError('timestamp must be an integer')
    if not isinstance(id, str) or not id:
        raise ValueError('id must be a nonempty string')
    raw = json.dumps([timestamp, id], separators=(',', ':'), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode('utf-8')).rstrip(b'=').decode('ascii')


def decode_cursor(cursor):
    if not isinstance(cursor, str) or not cursor:
        raise ValueError('cursor must be a nonempty string')
    if not _CURSOR_RE.fullmatch(cursor):
        raise ValueError('cursor has invalid characters')
    try:
        data = base64.urlsafe_b64decode(cursor + '=' * (-len(cursor) % 4))
        if base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii') != cursor:
            raise ValueError('non-canonical base64')
        value = json.loads(data.decode('utf-8'))
    except (binascii.Error, UnicodeDecodeError, RecursionError, ValueError) as exc:
        raise ValueError('malformed cursor') from exc
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('cursor must hold [timestamp, id]')
    timestamp, id = value
    if not _is_int(timestamp) or not isinstance(id, str) or not id:
        raise ValueError('cursor has invalid timestamp or id')
    return timestamp, id


def _validate_limit(limit):
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer between 1 and 100')


class Repository:
    def __init__(self, rows):
        self.rows = sorted(copy.deepcopy(list(rows)),
                           key=lambda row: (row['timestamp'], row['id']))

    def page(self, limit=20, cursor=None):
        _validate_limit(limit)
        after = decode_cursor(cursor) if cursor is not None else None
        items = [r for r in self.rows
                 if after is None or (r['timestamp'], r['id']) > after]
        more = len(items) > limit
        items = items[:limit]
        next_cursor = None
        if more:
            last = items[-1]
            next_cursor = encode_cursor(last['timestamp'], last['id'])
        return {'items': copy.deepcopy(items), 'next_cursor': next_cursor}

    def list_items(self, limit=20):
        return self.page(limit)['items']
