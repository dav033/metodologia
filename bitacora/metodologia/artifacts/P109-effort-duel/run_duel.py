"""Owner-authorized three-dossier medium/high comparison; no product execution.

Runs one call at a time per effective account, at most two accounts concurrently.
Only final answers and allowlisted numeric usage are saved, never private thinking.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'P109-review-ladder/run.py'
spec=importlib.util.spec_from_file_location('prior_review_harness',BASE)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
DEADLINE=900
ROUTES=[
    {'id':'sol-medium','profile':'codex-2','provider':'codex','model':'gpt-6.1-sol','effort':'medium'},
    {'id':'sol-high','profile':'codex-2','provider':'codex','model':'gpt-6.1-sol','effort':'high'},
    {'id':'sonnet-medium','profile':'claude-work','provider':'claude','model':'claude-sonnet-5-5','effort':'medium'},
    {'id':'sonnet-high','profile':'claude-work','provider':'claude','model':'claude-sonnet-5-5','effort':'high'}]
INSTRUCTION='''Analyze the complete supplied technical dossier: authoritative requirements, verified baseline guarantees, candidate code, traces and proposed plan. Cross their boundaries to find concrete failures. Historical memos do not override current requirements. Only explicitly verified baseline protections may be assumed correct; candidate snippets may contain defects.
Use only this input. Do not browse, call tools, inspect local files or execute code. You are reviewing, not implementing. Do not invent guarantees, requirements or missing baseline protections. Deduplicate root causes; a missing regression test for a defect belongs with that defect, not a second finding. A correct primitive can have an incorrect caller. Give a specific witness and minimal fix for each finding. Report uncertainty rather than asserting a failure that depends on unspecified facts. There may be correct design choices worth preserving; do not force a finding for every section.
Return ONLY one JSON object, no markdown/prose outside it, at most 12 independent findings and 1800 whitespace-delimited words:
{"verdict":"acceptable|needs_changes","findings":[{"task":"exact snippet/task ID","severity":"critical|high|medium|low","issue":"root cause","evidence":"specific cross-references from the dossier","failure_scenario":"minimal counterexample, trace or arithmetic","fix":"minimal sound correction"}],"uncertainties":["material unresolved issue, if any"]}.
Use English. A material proven defect requires needs_changes. State what the supplied evidence supports, without generic checklists.

DOSSIER:
'''

def save(path,data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    tmp.replace(path)

def validate_answer(text):
    try:answer=json.loads(text)
    except (ValueError,TypeError):return None,False
    if not isinstance(answer,dict):return answer,False
    findings=answer.get('findings');uncertainties=answer.get('uncertainties')
    valid=answer.get('verdict') in ('acceptable','needs_changes') and isinstance(findings,list) and len(findings)<=12
    valid=valid and isinstance(uncertainties,list) and all(isinstance(u,str) for u in uncertainties)
    for f in findings if isinstance(findings,list) else []:
        valid=valid and isinstance(f,dict) and all(isinstance(f.get(k),str) and f[k].strip() for k in ('task','severity','issue','evidence','failure_scenario','fix'))
        valid=valid and isinstance(f,dict) and f.get('severity') in ('critical','high','medium','low')
    return answer,bool(valid and len(text.split())<=1800)

def run_one(case,route):
    path=ROOT/f"{case['id']}-{route['id']}.json"
    if path.exists():
        old=json.loads(path.read_text())
        if old['status']=='completed':print('SKIP',path.name,flush=True);return True
        print('STOP existing unresolved record',path.name,old['status'],flush=True);return False
    prompt=INSTRUCTION+case['input']
    before=base.quota(route['profile'],route['provider'])
    record={'schema_version':1,'case':case['id'],'route':route,'status':'prepared','prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
            'prompt_characters':len(prompt),'quota_before':before,'deadline_seconds':DEADLINE,'started_at':time.time()}
    if any(w.get('used_percent',0)>=100 for n,w in before.get('windows',{}).items() if n in ('five_hour','seven_day')):
        record['status']='quota_exhausted';save(path,record);return False
    env={k:v for k,v in os.environ.items() if k not in ('CLAUDECODE','CLAUDE_CONFIG_DIR','CODEX_HOME')}
    env.update(base.bt_profiles.env_of(route['profile']))
    model=route['model'];effort=route['effort'];provider=route['provider']
    if provider=='codex':
        args=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--model',model,'-c',f'model_reasoning_effort="{effort}"','--json','-']
        stdin=prompt
    elif provider=='claude':
        args=['claude','--print','--model',model,'--effort',effort,'--safe-mode','--restricted','--tools','','--no-session-persistence','--permission-mode','plan','--output-format','stream-json','--verbose']
        stdin=prompt
    else:
        args=['agy','--model',model,'--mode','plan','--disable-slash-commands','--output-format','stream-json','--print-timeout',f'{DEADLINE}s','--print='+prompt]
        stdin=None
    record['status']='running';save(path,record)
    print('START',case['id'],route['id'],route['effort'],flush=True)
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='p109-effort-duel-') as cwd:
        try:
            p=subprocess.run(args,input=stdin,text=True,capture_output=True,cwd=cwd,env=env,timeout=DEADLINE+30)
            parsed=base.extract(provider,p.stdout)
            answer,valid=validate_answer(parsed.get('response_text',''))
            parsed.update(answer=answer,format_valid=valid,response_words=len(parsed.get('response_text','').split()))
            record.update(parsed,exit_code=p.returncode,status='completed' if p.returncode==0 else 'cli_error')
            if p.returncode!=0:record['error_excerpt']=p.stderr[-1000:]
            if provider=='claude' and parsed['observed_models']!=[model]:record['status']='model_identity_mismatch'
        except subprocess.TimeoutExpired:
            record.update(status='timeout',exit_code=None,usage_reported=None,format_valid=False)
    record['elapsed_seconds']=round(time.monotonic()-started,3)
    record['quota_after']=base.quota(route['profile'],provider)
    save(path,record)
    print('DONE',case['id'],route['id'],record['status'],record['elapsed_seconds'],'s','format='+str(record.get('format_valid')),'usage='+json.dumps(record.get('usage_reported')),flush=True)
    return record['status']=='completed'

def lane(provider,cases):
    routes=[r for r in ROUTES if r['provider']==provider]
    for i,case in enumerate(cases):
        ordered=routes if (i+(provider=='claude'))%2==0 else list(reversed(routes))
        for route in ordered:
            if not run_one(case,route):return {'provider':provider,'status':'stopped','case':case['id'],'route':route['id']}
    return {'provider':provider,'status':'complete'}

if __name__=='__main__':
    cases=json.loads((ROOT/'cases.json').read_text())
    oracle=json.loads((ROOT/'oracle-checks.json').read_text())
    digest=hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest()
    assert oracle['oracle_sha256']==digest and oracle['passed']==31
    protocol={'schema_version':1,'scope':'Owner-authorized hard analysis pilot, outside formal REQ-024 benchmark',
              'cases':3,'target_calls':12,'routes':ROUTES,'oracle_sha256':digest,'instruction':INSTRUCTION,
              'common_deadline_seconds':DEADLINE,'maximum_findings':12,'maximum_words':1800,
              'base_harness_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'concurrency':'one per effective account, maximum two accounts; effort order alternates per case and between accounts',
              'model_order':{'codex':[['medium','high'],['high','medium'],['medium','high']],'claude':[['high','medium'],['medium','high'],['high','medium']]},
              'grading':'Explicit coordinator mapping to 31 frozen root defects; accept grouped findings covering multiple roots; adjudicate supported extras separately; count duplicate coverage once; report groundedness and JSON reliability, not only recall.',
              'limitations':['One run per cell; self-contained synthetic dossiers, not production repository audits','Different hidden CLI contexts/tokenizers/cache accounting','Matched medium/high efforts per owner request; no repeated cells, so order/cache and sampling variation remain limitations','Quota is coarse account telemetry, may lag/include other account use; zero displayed delta is not zero cost']}
    if (ROOT/'protocol.json').exists():
        assert json.loads((ROOT/'protocol.json').read_text())['oracle_sha256']==digest
    else:save(ROOT/'protocol.json',protocol)
    versions={}
    for executable in ('codex','claude'):
        p=subprocess.run([executable,'--version'],capture_output=True,text=True,timeout=15)
        versions[executable]={'exit_code':p.returncode,'version':(p.stdout or p.stderr).strip()[:200]}
    save(ROOT/'runtime-versions.json',versions)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda provider:lane(provider,cases),('codex','claude')))
    save(ROOT/'execution-summary.json',results)
    print('EXECUTION SUMMARY',json.dumps(results),flush=True)
