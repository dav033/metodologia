import base64
import binascii
import json
import re

_CURSOR_PATTERN = re.compile(r'[A-Za-z0-9_-]+')


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
    if not _CURSOR_PATTERN.fullmatch(cursor):
        raise ValueError('cursor must use only unpadded URL-safe base64 characters')
    return _parse_pair(_load_payload(_b64decode(cursor)))


def _b64encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64decode(cursor):
    padded = cursor + '=' * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded)
    except binascii.Error as exc:
        raise ValueError('malformed base64 cursor') from exc
    # Rejects non-canonical encodings, so each tuple has exactly one token.
    if _b64encode(raw) != cursor:
        raise ValueError('malformed base64 cursor')
    return raw


def _load_payload(raw):
    try:
        return json.loads(raw.decode('utf-8'))
    except (ValueError, RecursionError) as exc:
        raise ValueError('malformed JSON cursor payload') from exc


def _parse_pair(payload):
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError('cursor must encode a [timestamp, id] pair')
    timestamp, row_id = payload
    _check_timestamp(timestamp)
    _check_id(row_id)
    return timestamp, row_id


def _check_timestamp(timestamp):
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise ValueError('timestamp must be an integer')


def _check_id(row_id):
    if not isinstance(row_id, str) or not row_id:
        raise ValueError('id must be a nonempty string')
    try:
        row_id.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ValueError('id must be valid UTF-8 text') from exc
