"""Foreground lifecycle proof using real controlling terminals and subprocesses."""
from __future__ import annotations

import json
import os
import signal
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestration_terminal_support import ForegroundHarness

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_orchestration_terminal as terminal


class ForegroundTests(ForegroundHarness, unittest.TestCase):
    def test_terminal_read_before_json_resumes_after_forced_background_stop(self):
        attempted = self.base / 'early-read'
        self.child.write_text(f'''
import json, os, sys
from pathlib import Path
fd=os.open('/dev/tty',os.O_RDWR)
Path({str(attempted)!r}).write_text('attempted')
read=os.read(fd,2).decode()
json.load(sys.stdin)
print(json.dumps(dict(read=read)),flush=True)
''')
        source = self.source({}, timeout=1).replace('before=termios.tcgetattr(0)', '''
before=termios.tcgetattr(0)
import time
original=os.tcsetpgrp
def delayed(fd,group):
    if group!=os.getpgrp():
        deadline=time.monotonic()+.5
        while time.monotonic()<deadline:
            state=Path('/proc/'+str(group)+'/stat').read_text().rsplit(')',1)[1].split()[0]
            if state=='T': break
            time.sleep(.01)
        assert state=='T', 'fixture did not force the SIGTTIN startup window'
    original(fd,group)
os.tcsetpgrp=delayed
''') + "\nassert not result['timed_out']\nassert json.loads(result['text'])['read']=='x\\n'\n"
        pid, fd = self.start(source)
        deadline = time.monotonic() + 3
        while not attempted.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(attempted.exists())
        os.write(fd, b'x\n')
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)

    def test_fresh_children_take_foreground_on_same_controlling_terminal(self):
        pid, fd = self.start(self.source({'scope': 'bounded'}, repeat=2))
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        rows = self.wait_rows(2)
        self.assertNotEqual(rows[0]['pid'], rows[1]['pid'])
        self.assertNotEqual(rows[0]['session_id'], rows[1]['session_id'])
        self.assertNotEqual(rows[0]['instance'], rows[1]['instance'])
        for row in rows:
            self.assertEqual(row['ppid'], pid)
            self.assertEqual(row['sid'], pid)
            self.assertEqual(row['pgid'], row['foreground'])
            self.assertEqual(row['pgid'], row['pid'])
            self.assertEqual(row['package'], {'scope': 'bounded'})
        self.assertIn('RESTORED', output)

    def test_terminal_interrupt_is_not_forwarded_twice_and_restores_termios(self):
        pid, fd = self.start(self.source({'hang': True}))
        self.wait_rows(1)
        os.write(fd, b'\x03')
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        self.assertIn('"stopped": true', output)
        self.assertIn('RESTORED', output)

    def test_direct_sigterm_stops_owned_child_and_restores_terminal(self):
        pid, fd = self.start(self.source({'hang': True}))
        self.wait_rows(1)
        os.kill(pid, signal.SIGTERM)
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        self.assertIn('"stopped": true', output)
        self.assertIn('RESTORED', output)

    def test_timeout_and_output_overflow_are_explicit_and_restore_terminal(self):
        for package, timeout, field in [({'hang': True}, .2, 'timed_out'), ({'overflow': True}, 3, 'overflow')]:
            with self.subTest(field=field):
                pid, fd = self.start(self.source(package, timeout=timeout))
                code, output = self.finish(pid, fd)
                self.assertEqual(code, 0, output)
                self.assertIn('"' + field + '": true', output)
                self.assertIn('RESTORED', output)

    def test_nonterminal_preflight_and_unsupported_backend_fail_closed(self):
        with self.assertRaisesRegex(terminal.TerminalError, 'CONTROLLING_TTY'):
            terminal.require_foreground(fd=-1)
        with self.assertRaisesRegex(terminal.TerminalError, 'NOT_ACTIVATED'):
            terminal.preflight(None)
        for value in ['["relative"]', '[1]', 'null', '{"argv":[]}']:
            with self.subTest(value=value), self.assertRaises(terminal.TerminalError):
                terminal.preflight(value)

    def test_no_signal_is_sent_to_foreign_process_group(self):
        source = self.source({'hang': True}, timeout=.15).replace(
            "before=termios.tcgetattr(0)",
            "before=termios.tcgetattr(0)\n"
            "original=os.killpg\n"
            "def owned(group,sig):\n"
            "    assert group != os.getpgrp(), 'unrelated foreground group was signalled'\n"
            "    original(group,sig)\n"
            "os.killpg=owned")
        pid, fd = self.start(source)
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        self.assertIn('RESTORED', output)

    def test_start_failure_restores_terminal_and_signal_handlers(self):
        source = '''
import os, signal, sys, termios
from pathlib import Path
import bt_orchestration_terminal as t
before=termios.tcgetattr(0)
handler=signal.getsignal(signal.SIGINT)
try:
    t.run_child([sys.executable,'-c','pass'],{},Path('/does-not-exist-req008'),dict(os.environ),timeout=1,output_bytes=256)
except FileNotFoundError: pass
else: raise AssertionError('startup failure was hidden')
assert termios.tcgetattr(0)==before
assert signal.getsignal(signal.SIGINT)==handler
print('RESTORED',flush=True)
'''
        pid, fd = self.start(source)
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        self.assertIn('RESTORED', output)

    def test_relay_parent_waits_for_planning_exit_before_fresh_children(self):
        supervisor = self.base / 'supervisor.py'
        supervisor.write_text(self.source({'scope': 'milestone'}, repeat=2).replace(
            'before=termios.tcgetattr(0)',
            "before=termios.tcgetattr(0)\n"
            "assert not Path('/proc/'+os.environ['PLANNER']).exists(), 'planner still alive'"))
        planner = self.base / 'planner.py'
        helper = self.base / 'helper.py'
        helper.write_text('''
import json, sys
from pathlib import Path
import bt_orchestration_transition as transition
data=json.loads(Path(sys.argv[1]).read_text())
transition.prepare(Path(sys.argv[1]),data['spec'],'planning-test',data['facts'])
''')
        planner.write_text(f'''
import ctypes, json, os, subprocess, sys, time
from pathlib import Path
import bt_relay as relay
import bt_relay_proc as proc
ctypes.CDLL(None).prctl(15,b'claude',0,0,0)
pid=os.getpid()
wrapper=int(os.environ['METODOLOGIA_RELAY_WRAPPER'])
request=relay.relay_dir()/'foreground-test.json'
facts=dict(pid=pid,start=proc.read(pid)['start'],wrapper=dict(pid=wrapper,start=proc.read(wrapper)['start']))
spec=dict(argv=[sys.executable,{str(supervisor)!r}],cwd={str(self.base)!r},env={{}},unset=[])
relay.write_private(request,json.dumps(dict(spec=spec,facts=facts)))
os.environ['PLANNER']=str(pid)
# relay's environment overlay is intentionally limited to account selectors.
path=Path({str(supervisor)!r})
path.write_text(path.read_text().replace("os.environ['PLANNER']",repr(str(pid))))
subprocess.Popen([sys.executable,{str(helper)!r},str(request)],start_new_session=True)
Path({str(self.base / 'ready')!r}).write_text(str(pid))
while True: time.sleep(.05)
''')
        source = f'''
import os, sys
os.environ['BITACORA_ROOT']={str(self.base / 'bitacora')!r}
os.execv(sys.executable,[sys.executable,{str(SCRIPTS / 'relay_run.py')!r},'planning','--',sys.executable,{str(planner)!r}])
'''
        pid, fd = self.start(source)
        deadline = time.monotonic() + 4
        while not (self.base / 'ready').exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue((self.base / 'ready').exists())
        self.assertFalse(self.rows.exists(), 'successor started before turn end')
        marker = self.base / 'bitacora/.state/relay/turn-ended-planning-test'
        marker.write_text('ended')
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        rows = self.wait_rows(2)
        self.assertEqual(rows[0]['sid'], pid)
        self.assertEqual(rows[0]['pgid'], rows[0]['pid'])
        self.assertNotEqual(rows[0]['session_id'], rows[1]['session_id'])

    def test_changed_wrapper_refuses_without_signalling(self):
        import bt_orchestration_transition as transition
        import bt_relay_launch as launcher

        facts = {'pid': os.getpid(), 'start': 1, 'wrapper': {'pid': 12, 'start': 34}}
        with patch.object(transition.client, 'verify_wrapper', return_value=False), \
                patch.object(launcher, 'stop_agent') as stop:
            with self.assertRaisesRegex(launcher.Refused, 'left intact'):
                transition.prepare(self.base / 'request', {'argv': [sys.executable], 'cwd': str(self.base)},
                                   'planning-test', facts)
            stop.assert_not_called()

    def test_existing_supervisor_dispatches_bounded_fresh_milestones_without_commits(self):
        source = f'''
import json, os, sys
from pathlib import Path
os.environ['BITACORA_ROOT']={str(self.base / 'supervised-root')!r}
import bt_core as core
import bt_run as engine
import bt_runentry as entry
import bt_runstate as rs
import bt_requirements_gate as gate
import bt_orchestration_context as context
import bt_orchestration_terminal as t
pdir=core.ROOT/'demo'
rdir=pdir/'requirements/REQ-001-demo'
rdir.mkdir(parents=True)
(pdir/'project.json').write_text(json.dumps(dict(repo={str(self.base)!r})))
(rdir/'SPEC.md').write_text('Approved controlled lifecycle proof')
(rdir/'PLAN.md').write_text('---\\nstatus: approved\\nexecution_contract: requirements-v1\\n---\\n'
    '# Plan\\n## Tasks\\n### M1 — First\\n- [ ] T1 — first · verify: `python -V`\\n'
    '### M2 — Second\\n- [ ] T2 — second · after: T1 · verify: `python -V`\\n## Progress log\\n')
review={{key:key+' reviewed' for key in gate.FIELDS}}
gate.record(rdir,{{**review,'evidence':['SPEC.md','PLAN.md'],'unresolved':[]}})
entry.keep_awake=lambda: None
engine.notify=lambda *args: None
def forbidden(*args): raise AssertionError('foreground must never auto-commit')
engine.commit_bitacora=forbidden
def route(project,state,task,unit):
    return dict(agent='claude',profile=None,model='controlled',effort='medium',kind='implement' if task else 'audit',tier=0)
def session(project,rdir,state,task,n,workdir,agent_cmd,unit,route):
    milestone=rs.unit_label(unit) if task else 'FINAL'
    package=context.build_package(rdir,state,unit,milestone)
    info=t.run_child([sys.executable,os.environ['CHILD']],package,workdir,dict(os.environ),timeout=3,output_bytes=1024)
    assert json.loads(info['text'])['session_id']
    assert not info['stopped'] and not info['overflow'] and info['rc']==0
    if task:
        def claim(current):
            for member in unit:
                rs.mark(current,member['id'],'in_progress',claimed_done=True,evidence='controlled lifecycle')
        rs.update(rdir,claim)
    else:
        (rdir/'REPORT.md').write_text('# Controlled report\\nVerification passed\\n')
    return dict(info,early_exit=False,**{{key:route[key] for key in ('agent','profile','model','effort','kind','tier')}})
runtime=t.ForegroundRuntime(session,route,lambda: None)
assert engine.supervise('demo','REQ-001',foreground=True,foreground_runtime=runtime,no_autostart=True,audit=False)==0
state=rs.load(rdir)
assert state['status']=='done'
assert state['sessions']==3
assert all(task['status']=='done' for task in state['tasks'])
assert state['orchestration_mode']=='foreground-v1'
assert (rdir/'REPORT.md').exists()
print('SUPERVISOR_VERIFIED',flush=True)
'''
        pid, fd = self.start(source)
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        self.assertIn('SUPERVISOR_VERIFIED', output)
        rows = self.wait_rows(3)
        self.assertEqual(len({row['pid'] for row in rows}), 3)
        self.assertEqual(len({row['session_id'] for row in rows}), 3)
        self.assertEqual([row['package']['tasks'][0]['id'] for row in rows[:2]], ['T1', 'T2'])

    def test_missing_parent_returns_exact_manual_checkout_command_without_effects(self):
        import bt_orchestration_transition as transition

        rdir = self.base / 'requirement'
        rdir.mkdir()
        (rdir / 'PLAN.md').write_text('---\nstatus: approved\n---\n')
        with patch.object(transition.core, 'find_req', return_value=rdir), \
                patch.object(transition.gate, 'require_ready', return_value={'status': 'ready'}), \
                patch.object(transition.state_, 'load', return_value=None), \
                patch.object(transition.core.ws, 'workdir', return_value=self.base), \
                patch.object(transition.client, 'locate', return_value={'wrapper': None, 'why': 'no parent'}), \
                patch.object(transition.subprocess, 'Popen') as spawn, \
                patch.object(transition.launcher, 'stop_agent') as stop:
            result = transition.launch('demo', 'REQ-001')
            self.assertEqual(result['decision'], 'manual')
            self.assertIn(str(SCRIPTS / 'bitacora.py'), result['command'])
            self.assertIn('run REQ-001 --foreground --no-autostart', result['command'])
            spawn.assert_not_called()
            stop.assert_not_called()

    def test_public_foreground_entry_fails_before_opening_or_reserving_a_run(self):
        import bt_requirements_gate as gate
        import bt_run as engine

        with patch.object(engine, 'find_req', return_value=self.base), \
                patch.object(gate, 'require_ready', return_value={'status': 'ready'}), \
                patch.object(engine.rs, 'load', return_value=None), \
                patch.object(terminal, 'configured_runtime', return_value=None), \
                patch.object(engine, '_open') as open_run:
            with self.assertRaisesRegex(SystemExit, 'FOREGROUND_RUNTIME_NOT_ACTIVATED'):
                engine.supervise('demo', 'REQ-001', foreground=True)
            open_run.assert_not_called()
        self.assertFalse((self.base / 'RUN.json').exists())

    def test_malformed_successor_and_missing_wrapper_never_signal(self):
        import bt_orchestration_transition as transition
        import bt_relay_launch as launcher

        for spec in ({'argv': [1], 'cwd': str(self.base)}, {'argv': [sys.executable], 'cwd': str(self.base)}):
            with self.subTest(spec=spec), patch.object(launcher, 'stop_agent') as stop:
                with self.assertRaises(launcher.Refused):
                    transition.prepare(self.base / 'request', spec, 'planning-test', {})
                stop.assert_not_called()

    def test_existing_successor_is_preserved_without_signalling(self):
        import bt_orchestration_transition as transition
        import bt_relay_launch as launcher

        pending = self.base / 'next-12.json'
        pending.write_text('existing quota successor')
        facts = {'pid': os.getpid(), 'start': 1, 'wrapper': {'pid': 12, 'start': 34}}
        with patch.object(transition.client, 'verify_wrapper', return_value=True), \
                patch.object(transition.relay, 'relay_dir', return_value=self.base), \
                patch.object(launcher, 'stop_agent') as stop:
            with self.assertRaisesRegex(launcher.Refused, 'already prepared'):
                transition.prepare(self.base / 'request', {'argv': [sys.executable], 'cwd': str(self.base)},
                                   'planning-test', facts)
            self.assertEqual(pending.read_text(), 'existing quota successor')
            stop.assert_not_called()

    def test_configured_worktree_is_rejected_before_opening_foreground_run(self):
        import bt_config
        import bt_requirements_gate as gate
        import bt_run as engine

        runtime = terminal.ForegroundRuntime(lambda: None, lambda: None, lambda: None)
        with patch.object(engine, 'find_req', return_value=self.base), \
                patch.object(gate, 'require_ready', return_value={'status': 'ready'}), \
                patch.object(engine.rs, 'load', return_value=None), \
                patch.object(terminal, 'preflight', return_value=runtime), \
                patch.object(bt_config, 'get', return_value='worktree'), \
                patch.object(engine, '_open') as open_run:
            with self.assertRaisesRegex(SystemExit, 'FOREGROUND_SERIAL_REQUIRED'):
                engine.supervise('demo', 'REQ-001', foreground=True)
            open_run.assert_not_called()
        with self.assertRaisesRegex(SystemExit, 'native batch dispatch is forbidden'):
            engine._run_batch('demo', self.base, {'foreground_runtime': runtime}, {}, [])

    def test_concurrent_successor_published_during_turn_wait_is_never_removed(self):
        import bt_relay_launch as launcher

        pending = self.base / 'next-12.json'
        def publish_then_refuse(*_args, **_kwargs):
            pending.write_text('foreign successor')
            raise launcher.Refused('turn did not end')
        with patch('bt_relay_client.verify_wrapper', return_value=True), \
                patch.object(launcher.relay, 'relay_dir', return_value=self.base), \
                patch.object(launcher, 'wait_turn_end', side_effect=publish_then_refuse), \
                patch.object(launcher, 'stop_agent') as stop:
            with self.assertRaisesRegex(launcher.Refused, 'turn did not end'):
                launcher.run_wrapper(self.base / 'handoff', 'test', str(self.base), 'planning-test',
                                     11, 22, (12, 34), True, successor={'argv': [sys.executable]})
            self.assertEqual(pending.read_text(), 'foreign successor')
            stop.assert_not_called()

    def test_descendant_surviving_parent_is_terminated_and_reaped(self):
        self.child.write_text('''
import json, os, subprocess, sys
json.load(sys.stdin)
subprocess.Popen([sys.executable,'-c', ''' + repr('''
import json, os, time
from pathlib import Path
fd=os.open('/dev/tty',os.O_RDWR)
Path(os.environ['ROWS']+'.descendant').write_text(json.dumps(dict(pid=os.getpid(),start=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19])))
while True: time.sleep(.05)
''') + '''])
''')
        source = self.source({}, timeout=.3).replace("print('RESTORED',flush=True)", '''
record=json.loads(Path(os.environ['ROWS']+'.descendant').read_text())
path=Path('/proc/'+str(record['pid'])+'/stat')
assert not path.exists() or path.read_text().rsplit(')',1)[1].split()[0]=='Z', 'descendant retains TTY while supervisor alive'
print('RESTORED',flush=True)
''')
        pid, fd = self.start(source)
        code, output = self.finish(pid, fd)
        self.assertEqual(code, 0, output)
        record = json.loads(Path(str(self.rows) + '.descendant').read_text())
        descendant = record['pid']
        try:
            path = Path(f'/proc/{descendant}/stat')
            self.assertTrue(not path.exists() or path.read_text().rsplit(')', 1)[1].split()[0] == 'Z',
                            'owned descendant is still alive and can retain the terminal')
        finally:
            path = Path(f'/proc/{descendant}/stat')
            if path.exists() and path.read_text().rsplit(')', 1)[1].split()[19] == record['start']:
                os.kill(descendant, signal.SIGKILL)

    def test_wrapper_reservation_excludes_another_helper_before_turn_wait(self):
        import bt_relay_launch as launcher
        from bt_relay_reservation import reserve

        with patch('bt_relay_client.verify_wrapper', return_value=True), \
                patch.object(launcher.relay, 'relay_dir', return_value=self.base), \
                patch.object(launcher, 'wait_turn_end') as wait, \
                patch.object(launcher, 'stop_agent') as stop, reserve(self.base / 'next-12.json'):
            with self.assertRaises(launcher.WrapperBusy):
                launcher.run_wrapper(self.base / 'handoff', 'test', str(self.base), 'planning-test',
                                     11, 22, (12, 34), True, successor={'argv': [sys.executable]})
            wait.assert_not_called()
            stop.assert_not_called()

    def test_busy_wrapper_cannot_fall_back_to_terminal_typing(self):
        import bt_relay_launch as launcher

        with patch.object(launcher.relay, 'relay_dir', return_value=self.base), \
                patch.object(launcher.relay, 'supervised', return_value=False), \
                patch.object(launcher.relay, 'settings', return_value={'enabled': True}), \
                patch.object(launcher.relay, 'log'), \
                patch.object(launcher, 'successor_command', return_value='manual command'), \
                patch.object(launcher, 'run_wrapper', side_effect=launcher.WrapperBusy('reserved')), \
                patch.object(launcher, 'preflight') as preflight, \
                patch.object(launcher, 'stop_agent') as stop:
            self.assertEqual(launcher.run(self.base / 'handoff', 'test', str(self.base), 'planning-test',
                                          'tmux', '%1', 11, 22, True, wrapper=(12, 34)), 'skipped')
            preflight.assert_not_called()
            stop.assert_not_called()

    def test_successful_turn_wait_cannot_overwrite_a_concurrent_successor(self):
        import bt_relay_launch as launcher

        pending = self.base / 'next-12.json'
        def publish(*_args, **_kwargs):
            pending.write_text('foreign successor')
        with patch('bt_relay_client.verify_wrapper', return_value=True), \
                patch.object(launcher.relay, 'relay_dir', return_value=self.base), \
                patch.object(launcher, 'wait_turn_end', side_effect=publish), \
                patch.object(launcher, 'stop_agent') as stop:
            with self.assertRaises(launcher.WrapperBusy):
                launcher.run_wrapper(self.base / 'handoff', 'test', str(self.base), 'planning-test',
                                     11, 22, (12, 34), True, successor={'argv': [sys.executable]})
            self.assertEqual(pending.read_text(), 'foreign successor')
            stop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
