"""Controlled PATH provider exercising actual CLI dispatch inside a real PTY."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from orchestration_terminal_support import SCRIPTS

CLAUDE = '''
import json, os, pathlib, subprocess, sys, time, uuid
if '--version' in sys.argv:
    print(os.environ.get('FIXTURE_VERSION','2.1.299')+' (Claude Code)')
    sys.exit(0)
if '--safe-mode' not in sys.argv:
    assert os.environ.get('BITACORA_EXECUTION_POLICY')=='restricted-v1'
    package=json.load(sys.stdin) if 'exec' in sys.argv else json.loads(sys.argv[-1])
    assert 'No commits' in package['delegation']['constraints']
    assert package['delegation']['brief']=='Implement only the assigned task'
    task=os.environ['BITACORA_TASK']
    run=json.loads(pathlib.Path(os.environ['FIXTURE_RDIR'],'RUN.json').read_text())
    dispatches=[record for record in run['orchestration_delegations'].values()
                if record.get('identity',{}).get('task')==task and record.get('session')==int(os.environ['BITACORA_SESSION'])]
    assert len(dispatches)==1 and dispatches[0]['identity']['run_id']==package['run_id']
    assert dispatches[0]['identity']['milestone']==package['milestone']
    assert dispatches[0]['route']['agent']==('codex' if 'exec' in sys.argv else 'claude')
    with open(os.environ['ROWS']+'.workers','a') as f:
        f.write(json.dumps(dict(task=task,session=os.environ['BITACORA_SESSION'],package=package))+'\\n')
    if not os.environ.get('FIXTURE_BROKEN'):
        pathlib.Path(os.environ['FIXTURE_WORK'],task+'.txt').write_text('implementation')
    if task=='FINAL':
        pathlib.Path(os.environ['FIXTURE_RDIR'],'REPORT.md').write_text('# Verified final report\\n')
    else:
        subprocess.run([sys.executable,os.environ['FIXTURE_CLI'],'--project','demo','task','done','REQ-001',task,
                        '--evidence','controlled worker completed '+task],check=True)
    if os.environ.get('FIXTURE_WORKER_LINGER'):
        time.sleep(20)
    print(json.dumps(dict(type='result',subtype='success',is_error=False,result='worker done')))
    sys.exit(0)
package=json.load(sys.stdin)
session=str(uuid.uuid4())
fd=os.open('/dev/tty',os.O_RDWR)
with open(os.environ['ROWS'],'a') as f:
    f.write(json.dumps(dict(session=session, pid=os.getpid(),sid=os.getsid(0),pgid=os.getpgrp(),
                           foreground=os.tcgetpgrp(fd),tty=os.ttyname(fd),package=package,argv=sys.argv))+'\\n')
if os.environ.get('FIXTURE_INTERRUPT'):
    import signal
    os.kill(os.getpid(),signal.SIGINT)
assert '--tools' in sys.argv and sys.argv[sys.argv.index('--tools')+1]==''
assert '--strict-mcp-config' in sys.argv
assert '--effort' in sys.argv and sys.argv[sys.argv.index('--effort')+1]=='medium'
receipts=package['receipts']
task=next((t['id'] for t in package['tasks'] if t['id'] not in receipts['completed']),'FINAL')
kinds=[e['kind'] for e in receipts['effects'] if e['task']==task]
kind=next((k for k in ('delegate','verify','document','finish') if k not in kinds),'finish')
text='Implement only the assigned task' if kind=='delegate' else 'Verified and documented assigned work'
epoch=receipts.get('epochs',{}).get(task,0)
action=dict(kind=kind,task=task,text=text,reference='',action_id=task+'-'+kind+('-rework'+str(epoch) if epoch else ''))
print(json.dumps(dict(type='system',subtype='init',session_id=session,claude_code_version='2.1.299',
                      model='claude-haiku-5-5',tools=[os.environ.get('FIXTURE_TOOL','StructuredOutput')],
                      mcp_servers=[],skills=[],slash_commands=[])))
print(json.dumps(dict(type='result',subtype='success',is_error=False,session_id=session,structured_output=action)))
'''


def prepare(base: Path) -> tuple[Path, Path, dict[str, str]]:
    import bt_requirements_gate as gate
    import bt_runstate as rs

    root = base / 'bitacora'
    rdir = root / 'demo' / 'requirements' / 'REQ-001-demo'
    rdir.mkdir(parents=True)
    (root / 'demo' / 'DECISIONS.md').write_text('# Decisions\n')
    work = base / 'work'
    work.mkdir()
    (root / 'demo' / 'project.json').write_text(json.dumps({'repos': {'skill': {'hint': str(work), 'remote': ''}}}))
    (rdir / 'SPEC.md').write_text('Build two scoped tasks with verified receipts.\n')
    verify = work / 'verify.py'
    verify.write_text("import os, sys, signal, json\nfrom pathlib import Path\nassert Path(sys.argv[1]+'.txt').read_text()=='implementation', 'missing or defective implementation'\np=Path('verify-'+sys.argv[1]); n=int(p.read_text()) if p.exists() else 0; p.write_text(str(n+1))\nif os.environ.get('FIXTURE_VERIFY_INTERRUPT')=='runtime' or (os.environ.get('FIXTURE_VERIFY_INTERRUPT')=='settlement' and n==1):\n snapshot=dict(rows=len(Path(os.environ['ROWS']).read_text().splitlines()),workers=len(Path(os.environ['ROWS']+'.workers').read_text().splitlines()),verifications={p.name:p.read_text() for p in Path.cwd().glob('verify-T*')}); Path(os.environ['ROWS']+'.verification-interrupt').write_text(json.dumps(snapshot)); os.kill(os.getpid(),signal.SIGINT)\nassert not (os.environ.get('FIXTURE_FAIL_SETTLE')==sys.argv[1] and n==1), 'independent settlement verification failed once'\np=Path('verify-count'); p.write_text(str(int(p.read_text())+1 if p.exists() else 1))\nprint('verified real fixture')\n")
    (rdir / 'PLAN.md').write_text('---\nstatus: approved\nexecution_contract: requirements-v1\n---\n'
                                 '## Tasks\n### M1 — Two tasks\n'
                                 f'- [ ] T1 — First · repo: skill · verify: `{sys.executable} {verify} T1`\n'
                                 f'- [ ] T2 — Second · repo: skill · after: T1 · verify: `{sys.executable} {verify} T2`\n'
                                 '\n## Progress log\n')
    gate.record(rdir, {**{key: 'approved ' + key for key in gate.FIELDS},
                       'evidence': ['SPEC.md', 'PLAN.md'], 'unresolved': []})
    state = rs.init_state('demo', rdir, 'claude', 'haiku', False, {}, [], False)
    state['context_policy'] = {'entry_bytes': 16384, 'runtime_bytes': 4096, 'checkpoint_bytes': 8192}
    rs.save(rdir, state)
    binary = base / 'bin'
    binary.mkdir()
    cli = binary / 'claude'
    cli.write_text('#!' + sys.executable + '\n' + CLAUDE)
    cli.chmod(0o700)
    environment = dict(os.environ, BITACORA_ROOT=str(root), PATH=str(binary) + os.pathsep + os.environ['PATH'],
                       FIXTURE_CLI=str(SCRIPTS / 'bitacora.py'), FIXTURE_WORK=str(work), FIXTURE_RDIR=str(rdir),
                       BITACORA_RUN_GRACE_SEC='0.1', BITACORA_RUN_BACKOFF_SEC='0.01')
    return rdir, work, environment
