"""Durable completion evidence and explicit supersession after failed verification."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from bt_orchestration_contract import ContextError, load_journal

REPORT_LIMIT = 262144


def report_binding(rdir: Path, run_id: str, *, started_at: float | None = None) -> dict | None:
    path = rdir / 'REPORT.md'
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            raw = stream.read(REPORT_LIMIT + 1)
            after = os.fstat(stream.fileno())
    except OSError:
        return None
    if (not raw or len(raw) > REPORT_LIMIT or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)
            or (started_at is not None and after.st_mtime < started_at - 1)):
        return None
    return {'schema': 1, 'run_id': run_id, 'artifact': 'REPORT.md', 'bytes': len(raw),
            'digest': hashlib.sha256(raw).hexdigest()}


def report_matches(rdir: Path, run_id: str, binding: object) -> bool:
    if (not isinstance(binding, dict) or set(binding) != {'schema', 'run_id', 'artifact', 'bytes', 'digest'}
            or type(binding['schema']) is not int or binding['schema'] != 1 or binding['run_id'] != run_id
            or binding['artifact'] != 'REPORT.md' or type(binding['bytes']) is not int
            or not 0 < binding['bytes'] <= REPORT_LIMIT or not isinstance(binding['digest'], str)
            or not re.fullmatch('[a-f0-9]{64}', binding['digest'])):
        return False
    return report_binding(rdir, run_id) == binding


def invalidations(state: dict, task_id: str) -> list[dict]:
    owner = state.get('final', {}) if task_id == 'FINAL' else next(
        (task for task in state['tasks'] if task['id'] == task_id), {})
    records = owner.get('orchestration_invalidations', [])
    if not isinstance(records, list) or len(records) > 128:
        raise ContextError('INVALID_COMPLETION_SUPERSESSION')
    for record in records:
        if (not isinstance(record, dict) or set(record) != {'schema', 'run_id', 'finish_digest', 'session', 'reason'}
                or type(record['schema']) is not int or record['schema'] != 1
                or record['run_id'] != state['context_run_id'] or type(record['session']) is not int
                or record['session'] < 1 or not isinstance(record['reason'], str) or not 0 < len(record['reason']) <= 1000
                or not isinstance(record['finish_digest'], str) or not re.fullmatch('[a-f0-9]{64}', record['finish_digest'])):
            raise ContextError('INVALID_COMPLETION_SUPERSESSION')
    return records


def validate_supersession(rdir: Path, state: dict, milestone: str, superseded: dict[str, str], authority: str) -> None:
    members = {task['id'] for task in state['tasks'] if task.get('milestone') == milestone and not task.get('synthetic')}
    scope = members or ({'FINAL'} if milestone == 'FINAL' else set(superseded))
    digest = hashlib.sha256(milestone.encode()).hexdigest()[:16]
    journal = load_journal(rdir / f'ACTIONS-{digest}.json', state['context_run_id'], authority, scope)
    for task, finish in superseded.items():
        if not any(record['finish_digest'] == finish for record in invalidations(state, task)):
            raise ContextError('UNPROVEN_COMPLETION_SUPERSESSION')
        if not any(effect.get('digest') == finish and effect.get('status') == 'complete'
                   and effect.get('action', {}).get('kind') == 'finish' and effect['action'].get('task') == task
                   and effect.get('receipt', {}).get('ok') is True
                   for effect in journal.get('effects', [])):
            raise ContextError('UNPROVEN_FINISH_SUPERSESSION')
