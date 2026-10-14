"""Schema-1 orchestration data contracts; independent of providers and effects."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

KINDS = ('read', 'delegate', 'verify', 'document', 'finish', 'yield')
ACTION_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['kind', 'task', 'text', 'reference', 'action_id'],
    'properties': {
        'kind': {'type': 'string', 'enum': list(KINDS)},
        'task': {'type': 'string', 'maxLength': 128},
        'text': {'type': 'string', 'maxLength': 2000},
        'reference': {'type': 'string', 'maxLength': 128},
        'action_id': {'type': 'string', 'minLength': 1, 'maxLength': 80},
    },
}


class ContextError(ValueError):
    """Invalid, stale or oversized orchestration state."""


class ContextPressure(ContextError):
    """Rotate/checkpoint before delivering an unadmitted result."""


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def byte_size(value: object) -> int:
    return len(encode(value).encode('utf-8'))


def validate_action(action: object, scope: set[str]) -> dict:
    if not isinstance(action, dict) or set(action) != set(ACTION_SCHEMA['required']):
        raise ContextError('INVALID_ACTION_FIELDS')
    if action['kind'] not in KINDS:
        raise ContextError('INVALID_ACTION_KIND')
    for field in ('task', 'text', 'reference', 'action_id'):
        value = action[field]
        if (not isinstance(value, str) or len(value) > ACTION_SCHEMA['properties'][field]['maxLength']
                or '\0' in value):
            raise ContextError('INVALID_ACTION_VALUE')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', action['action_id']) or action['task'] not in scope:
        raise ContextError('INVALID_ACTION_SCOPE')
    if byte_size(action) > 4096:
        raise ContextError('OVERSIZED_STRUCTURED_ACTION')
    return action


def load_journal(path: Path, run_id: str, authority: str, scope: set[str]) -> dict:
    if not path.exists():
        return {'schema': 1, 'run_id': run_id, 'authority': authority, 'decisions': 0, 'sessions': [], 'effects': []}
    with path.open('rb') as stream:
        raw = stream.read(262145)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ContextError('INVALID_EFFECT_JOURNAL') from exc
    if (len(raw) > 262144 or not isinstance(data, dict)
            or set(data) != {'schema', 'run_id', 'authority', 'decisions', 'sessions', 'effects'}
            or type(data['schema']) is not int or data['schema'] != 1 or data['run_id'] != run_id
            or data['authority'] != authority or type(data['decisions']) is not int
            or not 0 <= data['decisions'] <= 128 or not isinstance(data['sessions'], list)
            or len(data['sessions']) > data['decisions']
            or any(not isinstance(session, str) or not 1 <= len(session) <= 128 for session in data['sessions'])
            or len(set(data['sessions'])) != len(data['sessions'])
            or not isinstance(data['effects'], list) or len(data['effects']) > 128):
        raise ContextError('INVALID_EFFECT_JOURNAL')
    for effect in data['effects']:
        if (not isinstance(effect, dict) or set(effect) != {'action', 'digest', 'status', 'receipt'}
                or effect['status'] not in ('pending', 'complete')):
            raise ContextError('INVALID_EFFECT_JOURNAL')
        validate_action(effect['action'], scope)
        if effect['digest'] != hashlib.sha256(encode(effect['action']).encode()).hexdigest():
            raise ContextError('INVALID_EFFECT_DIGEST')
        if effect['status'] == 'complete' and (not isinstance(effect['receipt'], dict)
                                              or byte_size(effect['receipt']) > 4096):
            raise ContextError('INVALID_EFFECT_RECEIPT')
    return data
