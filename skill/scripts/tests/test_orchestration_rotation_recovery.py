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

    def test_settlement_failure_reopens_task_preserving_history_and_counters(self):
        _rdir, _work, environment = prepare(self.base)
        environment['FIXTURE_FAIL_SETTLE'] = 'T1'
        body = f'''
import subprocess
cli=[sys.executable,{str(SCRIPTS / 'bitacora.py')!r},'--project','demo','run','REQ-001',
     '--foreground','--once','--no-autostart','--no-audit']
assert subprocess.run(cli,check=False).returncode==0
state=rs.load(rdir)
assert rs.get_task(state,'T1')['status']=='todo',state
first_attempts=rs.get_task(state,'T1')['attempts']
journal=json.loads(next(rdir.glob('ACTIONS-*.json')).read_text())
first_decisions=journal['decisions']
old_effects=len(journal['effects'])
assert subprocess.run(cli+['--resume'],check=False).returncode==0
state=rs.load(rdir)
assert rs.get_task(state,'T1')['status']=='done',state
assert rs.get_task(state,'T1')['attempts']==first_attempts
journal=json.loads(next(rdir.glob('ACTIONS-*.json')).read_text())
assert journal['decisions']>first_decisions
assert len(journal['effects'])>old_effects
assert len(rs.get_task(state,'T1')['orchestration_invalidations'])==1
archives=list(rdir.glob('CHECKPOINT-*-revision-*.json'))
assert len(archives)==1
assert 'T1' in json.loads(archives[0].read_text())['completed']
current=json.loads(next(path for path in rdir.glob('CHECKPOINT-*.json') if '-revision-' not in path.name).read_text())
assert current['runtime']['sequence']>=json.loads(archives[0].read_text())['runtime']['sequence']
print('REOPENED_AND_REPAIRED',flush=True)
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=30)
        self.assertEqual(code, 0, output)
        workers = [json.loads(line) for line in Path(str(self.rows) + '.workers').read_text().splitlines()]
        self.assertEqual([worker['task'] for worker in workers], ['T1', 'T2', 'T1'])

    def test_worker_claim_then_grace_termination_still_finishes_after_verify(self):
        rdir, _work, environment = prepare(self.base)
        environment['FIXTURE_WORKER_LINGER'] = '1'
        body = f'''
import subprocess
assert subprocess.run([sys.executable,{str(SCRIPTS / 'bitacora.py')!r},'--project','demo','run','REQ-001',
 '--foreground','--once','--no-autostart','--no-audit'],check=False).returncode==0
assert all(task['status']=='done' for task in rs.load(rdir)['tasks'])
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=30)
        self.assertEqual(code, 0, output)
        journal = json.loads(next(rdir.glob('ACTIONS-*.json')).read_text())
        delegates = [effect['receipt'] for effect in journal['effects'] if effect['action']['kind'] == 'delegate']
        self.assertTrue(all(receipt['early_exit'] and receipt['rc'] == -15 and receipt['ok'] for receipt in delegates))

    def test_foreground_interrupt_stops_continuous_cli_without_starting_another_child(self):
        rdir, _work, environment = prepare(self.base)
        environment['FIXTURE_INTERRUPT'] = '1'
        body = f'''
import subprocess, termios
before=termios.tcgetattr(0)
result=subprocess.run([sys.executable,{str(SCRIPTS / 'bitacora.py')!r},'--project','demo','run','REQ-001',
 '--foreground','--no-autostart','--no-audit','--max-attempts','1'],timeout=5,check=False)
assert result.returncode==0,result
assert termios.tcgetattr(0)==before
assert os.tcgetpgrp(0)==os.getpgrp()
assert rs.load(rdir)['status']=='stopped'
assert rs.load(rdir)['control']=='stop'
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=8)
        self.assertEqual(code, 0, output)
        rows = self.wait_rows(1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads((rdir / 'RUN.json').read_text())['tasks'][0]['attempts'], 0)

    def interrupt_verify(self, phase):
        rdir, work, environment = prepare(self.base)
        environment['FIXTURE_VERIFY_INTERRUPT'] = phase
        body = f'''
import subprocess, termios
before=termios.tcgetattr(0)
result=subprocess.run([sys.executable,{str(SCRIPTS / 'bitacora.py')!r},'--project','demo','run','REQ-001',
 '--foreground','--no-autostart','--no-audit','--max-attempts','1'],timeout=7,check=False)
assert Path(os.environ['ROWS']+'.verification-interrupt').exists(), 'verify interrupt fixture never reached'
assert result.returncode==0,result
assert rs.load(rdir)['status']=='stopped'
assert rs.load(rdir)['control']=='stop'
assert all(task['attempts']==0 for task in rs.load(rdir)['tasks'])
assert termios.tcgetattr(0)==before
assert os.tcgetpgrp(0)==os.getpgrp()
'''
        code, output = self.finish(*self.start(self.source(environment, body)), timeout=10)
        self.assertEqual(code, 0, output)
        rows = self.wait_rows(2)
        marker = json.loads(Path(str(self.rows) + '.verification-interrupt').read_text())
        workers = [json.loads(line) for line in Path(str(self.rows) + '.workers').read_text().splitlines()]
        self.assertEqual(len(rows), marker['rows'])
        self.assertEqual(len(workers), marker['workers'])
        self.assertEqual({path.name: path.read_text() for path in work.glob('verify-T*')}, marker['verifications'])
        if phase == 'runtime':
            self.assertEqual([worker['task'] for worker in workers], ['T1'])
        self.assertIsNone(json.loads((rdir / 'RUN.json').read_text())['foreground_child'])

    def test_runtime_verify_interrupt_stops_before_next_reasoning_or_worker(self):
        self.interrupt_verify('runtime')

    def test_independent_settlement_verify_interrupt_does_not_count_failure(self):
        self.interrupt_verify('settlement')

    def test_recovered_native_route_reaches_settlement_and_independent_audit(self):
        _rdir, _work, environment = prepare(self.base)
        binary = self.base / 'bin' / 'codex'
        binary.write_text((self.base / 'bin' / 'claude').read_text())
        binary.chmod(0o700)
        body = '''
from unittest.mock import patch
import bt_orchestration_effects as effects
import bt_orchestration_context as context
import bt_run
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
assert bt_run._settle_unit('demo',rdir,[task],2,info,work)=={'T1':'done'}
state=rs.load(rdir)
assert rs.get_task(state,'T1')['last_route']['agent']=='codex'
assert rs.get_task(state,'T1')['last_route']['profile']=='codex'
audit=dict(id='M1-audit',kind='audit',synthetic=True,milestone='M1',after=['T1'],tier=0)
assert rs.builders_of(state,audit)=={'codex'}
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
        # Real native worker and task CLI; only the post-dispatch persistence fault is injected.
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
