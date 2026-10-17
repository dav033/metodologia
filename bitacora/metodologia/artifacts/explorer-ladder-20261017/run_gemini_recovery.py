"""One declared AGY permission repair: six cells in OS read-only sandbox."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixed_explorer_runner',ROOT/'run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
DEST=ROOT/'gemini-recovery'
assert not DEST.exists(), 'Do not repeat permission-repair attempts'
assert json.loads((ROOT/'gemini-sandbox-check.json').read_text())['status']=='passed'
old=[]
for cid in range(1,7):
    path=ROOT/f"E{cid}-gemini{'-a2' if cid==1 else ''}.json"
    r=json.loads(path.read_text())
    assert r['status']=='completed' and not r.get('response_text')
    r['included_in_comparison']=False;r['exclusion_reason']='AGY print mode soft-denied RunCommand; no final response, not a model-quality result'
    path.write_text(json.dumps(r,indent=2)+'\n');old.append(path.name)
DEST.mkdir()
(DEST/'source-hashes.json').write_text((ROOT/'source-hashes.json').read_text())
(ROOT/'protocol-gemini-recovery.json').write_text(json.dumps({
    'scope':'Exactly six permission-repair calls, original six preserved/excluded; no further retries',
    'excluded_records':old,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'imported_runner_sha256':hashlib.sha256((ROOT/'run.py').read_bytes()).hexdigest(),
    'same_prompts_and_source':True,'OS_sandbox':'read-only /, private /tmp, current cell read-only at /tmp/cell; .gemini native runtime state writable',
    'native_permissions':'Explicit skip tool confirmations, plan mode, no product execution requested. Filesystem source writes denied by OS.',
    'maximum_total_attempts':33,'stop_rule':'Stop repaired Gemini lane on first missing/invalid answer, provider failure or source change.',
    'comparability_caveat':'Native permission/tool contexts differ across providers; this repairs an integration blocker, not model reasoning.'
},indent=2)+'\n')
native_popen=subprocess.Popen
def sandboxed_popen(args,**kwargs):
    assert args[0]=='agy'
    cell=str(kwargs['cwd']);args=[a for a in args if a!='--sandbox']
    args.insert(1,'--dangerously-skip-permissions')
    args=['bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp',
          '--bind',str(Path.home()/'.gemini'),str(Path.home()/'.gemini'),
          '--ro-bind',cell,'/tmp/cell','--chdir','/tmp/cell','--',*args]
    kwargs['env']={**kwargs['env'],'GEMINI_DIR':str(Path.home()/'.gemini')}
    return native_popen(args,**kwargs)
m.subprocess.Popen=sandboxed_popen
m.ROOT=DEST
route=next(r for r in m.ROUTES if r['id']=='gemini')
cases=json.loads((ROOT/'cases.json').read_text())
finished=[]
for c in cases:
    ok=m.run_one(c,route)
    r=json.loads((DEST/f"{c['id']}-gemini{'-a2' if c['id']=='E1' else ''}.json").read_text())
    finished.append({'case':c['id'],'status':r['status'],'format_valid':r.get('format_valid')})
    if not ok or not r.get('format_valid'):
        print('STOP repaired lane: unresolved result',c['id'],flush=True);break
(DEST/'execution-summary.json').write_text(json.dumps(finished,indent=2)+'\n')
