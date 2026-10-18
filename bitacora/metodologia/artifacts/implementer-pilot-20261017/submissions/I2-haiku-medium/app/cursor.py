"""Opaque cursor codec for (timestamp, id) keyset pagination."""
import base64
import binascii
import json

_URL_SAFE_ALPHABET = frozenset(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
)


def validate_key(timestamp, id):
    """Raise ValueError unless (timestamp, id) is a valid pagination key."""
    if not isinstance(timestamp, int) or isinstance(timestamp, bool):
        raise ValueError('timestamp must be an integer')
    if not isinstance(id, str) or not id:
        raise ValueError('id must be a nonempty string')


def encode_cursor(timestamp, id):
    """Return an unpadded URL-safe base64 token for the pair (timestamp, id)."""
    validate_key(timestamp, id)
    payload = json.dumps([timestamp, id], separators=(',', ':'), ensure_ascii=False)
    return base64.urlsafe_b64encode(payload.encode('utf-8')).decode('ascii').rstrip('=')


def decode_cursor(cursor):
    """Return the (timestamp, id) pair encoded in a cursor token."""
    if not isinstance(cursor, str):
        raise ValueError('cursor must be a string')
    if not cursor:
        raise ValueError('cursor must not be empty')
    if not _URL_SAFE_ALPHABET.issuperset(cursor):
        raise ValueError('cursor contains characters outside the URL-safe base64 alphabet')
    if len(cursor) % 4 == 1:
        raise ValueError('cursor has invalid base64 length')
    try:
        raw = base64.urlsafe_b64decode(cursor + '=' * (-len(cursor) % 4))
    except binascii.Error as exc:
        raise ValueError('cursor is not valid base64') from exc
    if base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=') != cursor:
        raise ValueError('cursor is not canonical base64')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('cursor is not valid UTF-8') from exc
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('cursor is not valid JSON') from exc
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('cursor must encode a [timestamp, id] pair')
    timestamp, id = value
    validate_key(timestamp, id)
    return timestamp, id
