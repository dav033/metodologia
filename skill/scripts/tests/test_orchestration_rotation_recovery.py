"""Regression evidence for reviewed T4 crash, permission and settlement boundaries."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_orchestration_context as context_tests

# isort: split

import bt_core
import bt_hooks
import bt_orchestration_context as context
import bt_runstate as rs
from bt_orchestration_actions import ActionEngine
from bt_orchestration_effects import Executor
from orchestration_rotation_support import prepare
from orchestration_terminal_support import SCRIPTS, ForegroundHarness
from test_orchestration_rotation import action


class RecoveryCliTests(ForegroundHarness, unittest.TestCase):
    def source(self, environment, body):
        return f'''
import json, os, sys, time
from pathlib import Path
os.environ.update({environment!r})
sys.path.insert(0,{str(SCRIPTS)!r})
import bt_runstate as rs
import bt_orchestration_runtime as runtime
from bt_runsettle import settle_final
rdir=Path(os.environ['FIXTURE_RDIR'])
work=Path(os.environ['FIXTURE_WORK'])
route=dict(agent='claude',profile='claude',model='haiku',effort='medium',kind='audit',tier=0)
{body}
'''

    def test_final_crash_before_settlement_recovers_bound_report_without_rerunning_worker(self):
        _rdir, work, environment = prepare(self.base)
        for task_id in ('T1', 'T2'):
            (work / (task_id + '.txt')).write_text('implementation')
        body = '''
first=runtime.run_session('demo',rdir,rs.load(rdir),None,1,work,None,route=route)
assert first['orchestration_completed']==['FINAL'], first
report=rdir/'REPORT.md'
os.utime(report,(1,1))
second=runtime.run_session('demo',rdir,rs.load(rdir),None,2,work,None,route=route)
assert second['recovered'],second
assert settle_final('demo',rdir,2,second,time.time())=='done'
assert rs.load(rdir)['final']['done']
print('RECOVERED_FINAL',flush=True)
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=30)
        self.assertEqual(code, 0, output)
        workers = [json.loads(line) for line in Path(str(self.rows) + '.workers').read_text().splitlines()]
        self.assertEqual([worker['task'] for worker in workers], ['FINAL'])

    def test_final_report_changed_after_finish_is_rejected(self):
        _rdir, work, environment = prepare(self.base)
        for task_id in ('T1', 'T2'):
            (work / (task_id + '.txt')).write_text('implementation')
        body = '''
info=runtime.run_session('demo',rdir,rs.load(rdir),None,1,work,None,route=route)
assert info['orchestration_completed']==['FINAL'], info
(rdir/'REPORT.md').write_text('foreign report after validated finish')
assert settle_final('demo',rdir,1,info,time.time())=='failed'
assert not rs.load(rdir)['final'].get('done')
print('REPORT_DRIFT_REJECTED',flush=True)
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=30)
        self.assertEqual(code, 0, output)







    def test_recovered_native_route_reaches_settlement_and_independent_audit(self):
        _rdir, _work, environment = prepare(self.base)
        binary = self.base / 'bin' / 'codex'
        binary.write_text((self.base / 'bin' / 'claude').read_text())
        binary.chmod(0o700)
        body = '''
from unittest.mock import patch
import bt_orchestration_effects as effects
import bt_orchestration_context as context
from bt_runsettle import settle_task
import bt_runsession
from bt_orchestration_actions import ActionEngine
def action(kind,task='T1',text='',action_id='one'):
    return dict(kind=kind,task=task,text=text,reference='',action_id=action_id)
state=rs.load(rdir)
state.update(agent='codex',profile='codex',model='gpt-6-luna')
rs.save(rdir,state)
task=state['tasks'][0]
engine=ActionEngine(rdir,state,[task],'M1',context.Budget())
executor=effects.Executor('demo',rdir,state,[task],1,work,engine)
write=effects.atomic_json
def crash(path,data):
    if path.name.startswith('ORCHESTRATION-'): raise RuntimeError('injected receipt crash')
    write(path,data)
with patch.object(effects,'atomic_json',side_effect=crash):
    try: engine.execute(action('delegate',text='Implement only the assigned task'),executor)
    except RuntimeError: pass
    else: raise AssertionError('crash not injected')
engine=ActionEngine(rdir,rs.load(rdir),[task],'M1',context.Budget())
executor=effects.Executor('demo',rdir,rs.load(rdir),[task],2,work,engine)
engine.reconcile(executor.reconcile)
for kind in ('verify','document','finish'):
    engine.execute(action(kind,action_id=kind,text='Verified scoped work'),executor)
info=runtime.run_session('demo',rdir,rs.load(rdir),task,2,work,None,[task],route)
task_info={**info,**info['delegations']['T1']}
task_info.update(stopped=info['stopped'] or task_info.get('stopped',False),
                 timed_out=info['timed_out'] or task_info.get('timed_out',False),
                 rc=info['rc'] or task_info['rc'])
assert settle_task('demo',rdir,'T1',task_info['session'],task_info,work)=='done'
state=rs.load(rdir)
assert rs.get_task(state,'T1')['last_route']['agent']=='codex'
assert rs.get_task(state,'T1')['last_route']['profile']=='codex'
audit=dict(id='M1-audit',kind='audit',synthetic=True,milestone='M1',after=['T1'],tier=0)
assert rs.builders_of(state,audit)=={'codex'}
import bt_subscriptions
quota={name:dict(used_percent=20,resets_at=time.time()+3600,window_minutes=minutes)
       for name,minutes in (('five_hour',300),('seven_day',10080))}
with patch.object(bt_subscriptions,'read_claude',return_value=quota), \
     patch.object(bt_subscriptions,'read_codex',return_value=quota):
    audit_route=bt_runsession.session_route('demo',{**state,'pool':['codex','claude']},audit,[audit])
assert audit_route['agent']=='claude',audit_route
print('HONEST_RECOVERED_BUILDER',flush=True)
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=15)
        self.assertEqual(code, 0, output)


class RecoveryStateTests(unittest.TestCase):
    setUp = context_tests.OrchestrationContextTests.setUp

    def test_recovered_worker_keeps_predispatch_route_and_session(self):
        from bt_orchestration_storage import atomic_json as write_json
        # Real native worker and controlled completion claim; only the post-dispatch persistence fault is injected.
        base = self.rdir / 'native'
        base.mkdir()
        rdir, work, environment = prepare(base)
        environment['ROWS'] = str(base / 'rows.jsonl')
        state = rs.load(rdir)
        state.update(agent='codex', profile='codex', model='gpt-6-luna')
        rs.save(rdir, state)
        binary = base / 'bin' / 'codex'
        binary.write_text((base / 'bin' / 'claude').read_text())
        binary.chmod(0o700)
        task = state['tasks'][0]
        engine = ActionEngine(rdir, state, [task], 'M1', context.Budget())
        executor = Executor('demo', rdir, state, [task], 1, work, engine)
        def crash_after_worker(path, data):
            if path.name.startswith('ORCHESTRATION-'):
                raise RuntimeError('crash after worker claim')
            return write_json(path, data)
        with patch.dict(os.environ, environment), \
                patch('bt_orchestration_effects.atomic_json', side_effect=crash_after_worker), \
                self.assertRaisesRegex(RuntimeError, 'crash after worker claim'):
            engine.execute(action('delegate', text='Implement only the assigned task'), executor)
        restarted = ActionEngine(rdir, rs.load(rdir), [task], 'M1', context.Budget())
        restarted.reconcile(Executor('demo', rdir, rs.load(rdir), [task], 2, work, restarted).reconcile)
        receipt = restarted.journal['effects'][0]['receipt']
        self.assertEqual((receipt['agent'], receipt['profile'], receipt['model']), ('codex', 'codex', 'gpt-6-luna'))
        self.assertEqual(receipt['session'], 1)
        self.assertTrue(receipt['ok'])
        self.assertIsNone(receipt['rc'])

    def test_unproven_checkpoint_supersession_cannot_rewrite_history(self):
        rs.save(self.rdir, self.state)
        engine = ActionEngine(self.rdir, self.state, [self.task], 'M1', context.Budget())
        engine.decision_started()
        for kind in ('delegate', 'verify', 'document', 'finish'):
            engine.execute(action(kind, action_id=kind), lambda *_: {'ok': True})
        first = engine.checkpoint()
        engine.invalidate_finish('T1', 2, 'Independent verification failed; retained verify.log evidence')
        with self.assertRaisesRegex(context.ContextError, 'UNPROVEN_COMPLETION_SUPERSESSION'):
            context.save_checkpoint(self.rdir, engine.state, 'M1', completed=[], remaining=['T1'],
                                    delegation_refs=[], evidence_refs=[], budget=engine.budget,
                                    expected_revision=first['revision'], superseded={'T1': '0' * 64})
        self.assertEqual(context.load_checkpoint(self.rdir, self.state, 'M1'), first)
        second = engine.checkpoint()
        self.assertEqual(second['remaining'], ['T1'])
        self.assertEqual(second['revision'], first['revision'] + 1)
        self.assertEqual(engine.journal['decisions'], 1)
        archive = next(self.rdir.glob('CHECKPOINT-*-revision-*.json'))
        self.assertEqual(json.loads(archive.read_text()), first)


class RestrictedHookTests(unittest.TestCase):
    setUp = context_tests.OrchestrationContextTests.setUp

    def test_restricted_hooks_preserve_day_and_checkpoints_without_pull_commit_or_push(self):
        day = self.rdir / 'day.md'
        original = '# Day\n\n---\n\n## Session `worker`\n\n' + bt_core.render('SESSION.md')
        day.write_text(original)
        data = {'session_id': 'worker', 'cwd': str(self.rdir), 'source': 'startup'}
        with patch.dict(os.environ, BITACORA_EXECUTION_POLICY='restricted-v1'), \
                patch.object(bt_hooks, '_read_stdin_json', return_value=data), \
                patch.object(bt_hooks, 'resolve_project', return_value='demo'), \
                patch.object(bt_hooks, 'day_paths', return_value={'day': day}), \
                patch.object(bt_hooks, 'build_context', return_value='bounded context'), \
                patch.object(bt_hooks, '_git', return_value=None), \
                patch.object(bt_hooks, 'in_hq', return_value=False), \
                patch.object(bt_hooks, 'dirty_since_log', return_value=(False, '')), \
                patch.object(bt_hooks, 'write_index'), patch.object(bt_hooks, 'write_global_index'), \
                patch('bt_pending.sort_file'), patch('bt_continuation.save_checkpoint') as checkpoint, \
                patch('bt_vcs.pull') as pull, patch('bt_vcs.commit') as commit, patch('bt_vcs.push_async') as push, \
                contextlib.redirect_stdout(io.StringIO()):
            bt_hooks.hook_start()
            bt_hooks.hook_stop('codex')
            bt_hooks.hook_end()
            pull.assert_not_called()
            commit.assert_not_called()
            push.assert_not_called()
            self.assertEqual(checkpoint.call_count, 2)
        self.assertEqual(day.read_text(), original)


if __name__ == '__main__':
    unittest.main()
