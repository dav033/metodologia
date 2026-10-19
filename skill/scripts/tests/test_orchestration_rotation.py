"""Behavioral evidence for structured decisions, admitted receipts and safe resume."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_orchestration_context as context_tests

# isort: split

import bt_orchestration_context as context
import bt_orchestration_identity as identity
import bt_orchestration_provider as provider
import bt_orchestration_runtime as runtime
import bt_runstate as rs
from bt_orchestration_actions import ActionEngine, ActionError


def action(kind, task='T1', text='', reference='', action_id='one'):
    return {'kind': kind, 'task': task, 'text': text, 'reference': reference, 'action_id': action_id}


class RotationTests(unittest.TestCase):
    setUp = context_tests.OrchestrationContextTests.setUp
    def engine(self):
        return ActionEngine(self.rdir, self.state, [self.task], 'M1', context.Budget())

    def test_actions_reject_unknown_fields_and_unassigned_tasks(self):
        for invalid in ({**action('delegate'), 'argv': ['rm']}, action('delegate', task='T2'), action('commit')):
            with self.assertRaises(ActionError):
                self.engine().validate(invalid)

    def test_effect_receipt_is_reused_after_restart_without_duplicate_delegate(self):
        calls = []
        engine = self.engine()
        result = engine.execute(action('delegate'), lambda *_: calls.append('worker') or {'ok': True})
        restarted = self.engine()
        self.assertEqual(restarted.execute(action('delegate'), lambda *_: self.fail('duplicate worker')), result)
        self.assertEqual(calls, ['worker'])
        with self.assertRaisesRegex(ActionError, 'reuse'):
            restarted.execute(action('verify'), lambda *_: {})

    def test_unfinished_effect_is_not_replayed_after_crash(self):
        engine = self.engine()
        with self.assertRaisesRegex(RuntimeError, 'crash'):
            engine.execute(action('delegate'), lambda *_: (_ for _ in ()).throw(RuntimeError('crash')))
        with self.assertRaisesRegex(ActionError, 'UNRECONCILED_EFFECT'):
            self.engine().execute(action('delegate'), lambda *_: self.fail('replayed'))

    def test_finish_requires_delegate_verify_and_documentation(self):
        engine = self.engine()
        with self.assertRaisesRegex(ActionError, 'evidence'):
            engine.execute(action('finish'), lambda *_: {})
        for kind in ('delegate', 'verify', 'document'):
            engine.execute(action(kind, action_id=kind), lambda *_: {'ok': True})
        engine.execute(action('finish', action_id='finish'), lambda *_: {'ok': True})
        self.assertEqual(engine.completed(), ['T1'])

    def test_receipts_under_pressure_checkpoint_before_fresh_successor(self):
        engine = self.engine()
        engine.budget = context.Budget(context.BudgetPolicy(runtime_bytes=256))
        engine.execute(action('delegate'), lambda *_: {'ok': True, 'detail': 'é' * 100})
        with self.assertRaises(context.ContextPressure):
            engine.deliver()
        checkpoint = engine.checkpoint()
        successor = context.Budget(engine.budget.policy, **checkpoint['runtime']).successor()
        self.assertEqual(successor.generation, 1)
        self.assertEqual(successor.used_bytes, 0)
        self.assertEqual(self.engine().completed(), [])

    def test_orphan_checkpoint_lock_does_not_block_resume(self):
        context.checkpoint_path(self.rdir, 'M1').with_suffix('.lock').write_text('orphan')
        saved = self.engine().checkpoint()
        self.assertEqual(saved['revision'], 1)

    def test_resume_preserves_decision_budget_and_provider_session_identity(self):
        engine = self.engine()
        engine.decision_started()
        engine.session_finished('fresh-session')
        resumed = self.engine()
        self.assertEqual(resumed.journal['decisions'], 1)
        resumed.decision_started()
        with self.assertRaisesRegex(ActionError, 'REUSED_PROVIDER_SESSION'):
            resumed.session_finished('fresh-session')

    def test_new_work_invalidates_old_verification_and_documentation(self):
        engine = self.engine()
        for kind in ('delegate', 'verify', 'document', 'delegate'):
            engine.execute(action(kind, action_id=str(len(engine.journal['effects']))), lambda *_: {'ok': True})
        with self.assertRaisesRegex(ActionError, 'evidence'):
            engine.execute(action('finish', action_id='finish'), lambda *_: {'ok': True})

    def test_old_run_adoption_rejects_unbound_evidence_then_preserves_identity(self):
        old = {key: value for key, value in self.state.items() if key != 'context_run_id'}
        rs.save(self.rdir, old)
        evidence = context.checkpoint_path(self.rdir, 'M1')
        evidence.write_text('{}')
        with self.assertRaisesRegex(ActionError, 'UNBOUND_CONTEXT_EVIDENCE'):
            runtime.adopt_run(self.rdir, old)
        # Use a separate clean requirement; preserve the evidence being rejected.
        clean = self.rdir / 'clean'
        clean.mkdir()
        rs.save(clean, old)
        adopted = runtime.adopt_run(clean, old)
        self.assertTrue(adopted['context_run_id'])
        self.assertEqual(runtime.adopt_run(clean, adopted)['context_run_id'], adopted['context_run_id'])

    def test_partial_settlement_resume_keeps_completed_effects_in_scope(self):
        engine = self.engine()
        for kind in ('delegate', 'verify', 'document', 'finish'):
            engine.execute(action(kind, action_id=kind), lambda *_: {'ok': True})
        self.task['status'] = 'done'
        another = {**self.task, 'id': 'T2', 'status': 'todo'}
        self.state['tasks'].append(another)
        resumed = ActionEngine(self.rdir, self.state, [another], 'M1', context.Budget())
        self.assertEqual(resumed.completed(), ['T1'])
        self.assertEqual(resumed.checkpoint()['remaining'], ['T2'])
        with self.assertRaisesRegex(ActionError, 'INVALID_ACTION_SCOPE'):
            resumed.execute(action('delegate', task='T1', action_id='outside-unit'),
                            lambda *_: self.fail('scope widened'))

    def test_owned_orphan_is_signalled_only_through_pinned_descriptors(self):
        environment = dict(os.environ, BITACORA_PROJECT='test', BITACORA_RUN=self.state['req'],
                           BITACORA_ORCHESTRATOR_INSTANCE='owned-instance')
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'], env=environment, process_group=0)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        rs.save(self.rdir, self.state)
        identity.track(self.rdir, 'test', self.state, child.pid, 'owned-instance')
        with patch.object(identity.os, 'killpg') as numeric_signal:
            identity.recover(self.rdir, 'test', rs.load(self.rdir))
            numeric_signal.assert_not_called()
        self.assertEqual(child.wait(timeout=2), -signal.SIGKILL)
        self.assertIsNone(rs.load(self.rdir)['foreground_child'])

    def test_orphan_exit_during_identity_checks_never_signals_a_numeric_group(self):
        environment = dict(os.environ, BITACORA_PROJECT='test', BITACORA_RUN=self.state['req'],
                           BITACORA_ORCHESTRATOR_INSTANCE='exit-instance')
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'], env=environment, process_group=0)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        rs.save(self.rdir, self.state)
        identity.track(self.rdir, 'test', self.state, child.pid, 'exit-instance')
        original = signal.pidfd_send_signal
        def exit_before_signal(fd, sig):
            if sig == signal.SIGSTOP:
                child.kill()
                child.wait(timeout=2)
                raise ProcessLookupError
            return original(fd, sig)
        with patch.object(identity.os, 'killpg') as numeric_signal, \
                patch.object(identity.signal, 'pidfd_send_signal', side_effect=exit_before_signal):
            identity.recover(self.rdir, 'test', rs.load(self.rdir))
            numeric_signal.assert_not_called()




class ProviderTests(unittest.TestCase):
    def rows(self, **inventory):
        init = dict(type='system', subtype='init', session_id='session-1', claude_code_version='2.1.299',
                    model='claude-haiku-5-5', tools=['StructuredOutput'], mcp_servers=[], skills=[], slash_commands=[], **inventory)
        return [init, {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': 'session-1',
                           'structured_output': action('yield')}]

    def test_effective_inventory_and_identity_are_required(self):
        good = self.rows()
        self.assertEqual(provider.parse_stream('\n'.join(map(json.dumps, good)))[0], 'session-1')
        for field, value in [('tools', ['Read']), ('skills', ['loader']), ('mcp_servers', ['server']),
                             ('claude_code_version', '2.0.0')]:
            bad = self.rows()
            bad[0][field] = value
            with self.assertRaises(provider.ProviderError):
                provider.parse_stream('\n'.join(map(json.dumps, bad)))
        good[1]['session_id'] = 'foreign'
        with self.assertRaises(provider.ProviderError):
            provider.parse_stream('\n'.join(map(json.dumps, good)))

    def test_unexpected_tool_invocations_are_rejected(self):
        rows = self.rows()
        rows.insert(1, {'type': 'assistant', 'session_id': 'session-1',
                            'message': {'content': [{'type': 'tool_use', 'name': 'Read', 'input': {}}]}})
        with self.assertRaises(provider.ProviderError):
            provider.parse_stream('\n'.join(map(json.dumps, rows)))


if __name__ == '__main__':
    unittest.main()
