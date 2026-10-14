"""Admitted structured effects with durable, non-replayable delegation receipts."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from bt_orchestration_context import (
    Budget,
    ContextError,
    _locked,
    byte_size,
    encode,
    save_checkpoint,
)
from bt_orchestration_contract import load_journal, validate_action
from bt_requirements_gate import require_ready


class ActionError(ContextError):
    """Invalid scope, missing evidence or an unreconciled external effect."""


class ActionEngine:
    def __init__(self, rdir: Path, state: dict, unit: list[dict], milestone: str, budget: Budget) -> None:
        self.rdir, self.state, self.unit, self.milestone, self.budget = rdir, state, unit, milestone, budget
        digest = hashlib.sha256(milestone.encode()).hexdigest()[:16]
        self.path = rdir / f'ACTIONS-{digest}.json'
        members = [task for task in state['tasks'] if task.get('milestone') == milestone and not task.get('synthetic')]
        self.ids = {task['id'] for task in members or unit} or {'FINAL'}
        self.assigned_ids = {task['id'] for task in unit} or {'FINAL'}
        self.base_completed = {task['id'] for task in members if task.get('status') == 'done'}
        self.authority = hashlib.sha256(encode(require_ready(rdir)['snapshot']).encode()).hexdigest()
        self.journal = self._load()
        self.revision = 0

    def _load(self) -> dict:
        try:
            return load_journal(self.path, self.state['context_run_id'], self.authority, self.ids)
        except ContextError as exc:
            raise ActionError(str(exc)) from exc

    def _save(self) -> None:
        from bt_orchestration_storage import atomic_json
        if byte_size(self.journal) > 262144:
            raise ActionError('EFFECT_JOURNAL_LIMIT')
        atomic_json(self.path, self.journal)

    def validate(self, action: object, *, historical: bool = False) -> dict:
        try:
            return validate_action(action, self.ids if historical else self.assigned_ids)
        except ContextError as exc:
            raise ActionError(str(exc)) from exc

    def decision_started(self) -> None:
        with _locked(self.path):
            self.journal = self._load()
            if self.journal['decisions'] >= 128:
                raise ActionError('RECOVERABLE_STALL: durable decision cap reached')
            self.journal['decisions'] += 1
            self._save()

    def session_finished(self, session: str) -> None:
        with _locked(self.path):
            self.journal = self._load()
            if session in self.journal['sessions']:
                raise ActionError('REUSED_PROVIDER_SESSION: fresh invocation required')
            self.journal['sessions'].append(session)
            self._save()

    def reconcile(self, reconcile_effect: Callable[[dict], dict]) -> None:
        with _locked(self.path):
            self.journal = self._load()
            for effect in self.journal['effects']:
                if effect['status'] == 'pending':
                    result = reconcile_effect(effect['action'])
                    if not isinstance(result, dict) or byte_size(result) > 4096:
                        raise ActionError('INVALID_RECONCILIATION_RECEIPT')
                    effect.update(status='complete', receipt={'action_id': effect['action']['action_id'],
                                                             'kind': effect['action']['kind'],
                                                             'task': effect['action']['task'], **result})
            self._save()

    def completed(self) -> list[str]:
        return sorted(self.base_completed | {effect['action']['task'] for effect in self.active_effects()
                       if effect['status'] == 'complete' and effect['action']['kind'] == 'finish'
                       and effect['receipt'].get('ok') is True})

    def active_effects(self) -> list[dict]:
        from bt_orchestration_completion import invalidations
        cuts = {}
        for task_id in self.ids:
            revoked = {record['finish_digest'] for record in invalidations(self.state, task_id)}
            cuts[task_id] = max((index for index, effect in enumerate(self.journal['effects'])
                                if effect['digest'] in revoked and effect['action']['task'] == task_id), default=-1)
        return [effect for index, effect in enumerate(self.journal['effects'])
                if index > cuts[effect['action']['task']]]

    def invalidate_finish(self, task_id: str, session: int, reason: str) -> None:
        import bt_runstate as rs
        from bt_orchestration_completion import invalidations
        finish = next((effect for effect in reversed(self.active_effects())
                       if effect['action']['kind'] == 'finish' and effect['action']['task'] == task_id
                       and effect['status'] == 'complete' and effect['receipt'].get('ok') is True), None)
        if finish is None:
            return
        record = {'schema': 1, 'run_id': self.state['context_run_id'], 'finish_digest': finish['digest'],
                  'session': session, 'reason': reason}
        def invalidate(current):
            records = invalidations(current, task_id)
            if not any(item['finish_digest'] == record['finish_digest'] for item in records):
                if len(records) >= 128:
                    raise ActionError('COMPLETION_SUPERSESSION_CAP')
                owner = current.setdefault('final', {}) if task_id == 'FINAL' else rs.get_task(current, task_id)
                if task_id == 'FINAL':
                    owner.setdefault('attempts', 0)
                owner['orchestration_invalidations'] = [*records, record]
        self.state = rs.update(self.rdir, invalidate)

    def final_report_is_valid(self) -> bool:
        from bt_orchestration_completion import report_matches
        if 'FINAL' not in self.completed():
            return False
        self._require_evidence('FINAL')
        finish = next(effect for effect in reversed(self.active_effects()) if effect['action']['kind'] == 'finish')
        return report_matches(self.rdir, self.state['context_run_id'], finish['receipt'].get('report'))

    def _require_evidence(self, task: str) -> None:
        effects = [effect for effect in self.active_effects() if effect['action']['task'] == task]
        delegates = [index for index, effect in enumerate(effects) if effect['action']['kind'] == 'delegate']
        latest = delegates[-1] if delegates else len(effects)
        relevant = effects[latest:]
        verifies = [index for index, effect in enumerate(relevant) if effect['action']['kind'] == 'verify']
        documents = [index for index, effect in enumerate(relevant) if effect['action']['kind'] == 'document']
        if not (relevant and verifies and documents and verifies[-1] < documents[-1]
                and all(relevant[index]['status'] == 'complete' and relevant[index]['receipt'].get('ok') is True
                        for index in (0, verifies[-1], documents[-1]))):
            raise ActionError('Finish requires delegated verification and documentation evidence')

    def execute(self, action: dict, executor: Callable[[dict], dict]) -> dict:
        self.validate(action)
        with _locked(self.path):
            self.journal = self._load()
            digest = hashlib.sha256(encode(action).encode()).hexdigest()
            for effect in self.journal['effects']:
                if effect['action']['action_id'] == action['action_id']:
                    if effect['digest'] != digest:
                        raise ActionError('Action ID reuse with different effect')
                    if effect['status'] == 'pending':
                        raise ActionError('UNRECONCILED_EFFECT: inspect durable worker/state evidence before resume')
                    if effect not in self.active_effects():
                        raise ActionError('SUPERSEDED_ACTION_ID: retain history; choose a fresh action ID')
                    return effect['receipt']
            if len(self.journal['effects']) >= 128:
                raise ActionError('EFFECT_ATTEMPT_LIMIT')
            if any(effect['status'] == 'pending' for effect in self.journal['effects']):
                raise ActionError('UNRECONCILED_EFFECT: no new effects until pending operation is reconciled')
            if action['kind'] == 'finish':
                self._require_evidence(action['task'])
            if action['task'] in self.completed():
                raise ActionError('COMPLETED_TASK_EFFECT_FORBIDDEN')
            effect = {'action': action, 'digest': digest, 'status': 'pending', 'receipt': None}
            self.journal['effects'].append(effect)
            self._save()
            result = executor(action)
            if not isinstance(result, dict) or byte_size(result) > 4096:
                raise ActionError('OVERSIZED_EFFECT_RECEIPT: evidence retained externally; inspect pending effect')
            effect.update(status='complete', receipt={'action_id': action['action_id'], 'kind': action['kind'],
                                                     'task': action['task'], **result})
            self._save()
            return effect['receipt']

    def deliver(self) -> dict:
        from bt_orchestration_completion import invalidations
        effects = [effect for effect in self.active_effects() if effect['status'] == 'complete']
        receipt = {'completed': self.completed(), 'evidence': str(self.path),
                   'epochs': {task: len(invalidations(self.state, task)) for task in self.assigned_ids},
                   'effects': [{'id': effect['action']['action_id'], 'kind': effect['action']['kind'],
                                'task': effect['action']['task'], 'ok': effect['receipt'].get('ok')}
                               for effect in effects], 'latest': effects[-1]['receipt'] if effects else None,
                   'errors': [effect['receipt'] for effect in effects if effect['receipt'].get('ok') is False]}
        self.budget.admit(receipt)
        return receipt

    def checkpoint(self) -> dict:
        from bt_orchestration_completion import invalidations
        from bt_orchestration_context import load_checkpoint
        previous = load_checkpoint(self.rdir, self.state, self.milestone, self.budget.policy)
        undone = set(previous['completed'] if previous else []) - set(self.completed())
        superseded = {task: invalidations(self.state, task)[-1]['finish_digest'] for task in undone}
        checkpoint = save_checkpoint(self.rdir, self.state, self.milestone, completed=self.completed(),
                                     remaining=sorted(self.ids - set(self.completed())),
                                     delegation_refs=[str(self.path)], evidence_refs=[str(self.path)],
                                     budget=self.budget, expected_revision=self.revision, superseded=superseded)
        self.revision = checkpoint['revision']
        return checkpoint
