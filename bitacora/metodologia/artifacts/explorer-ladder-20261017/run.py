"""Run 24 authorized read-only Explorer cells, once each, on frozen real code."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'P109-review-ladder/run.py'
spec=importlib.util.spec_from_file_location('explorer_collectors',BASE)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
WORK=Path(json.loads((ROOT/'workspace.json').read_text())['root'])
DEADLINE=900
ROUTES=[
    {'id':'luna','profile':'codex-2','provider':'codex','model':'gpt-6-luna','effort':'high'},
    {'id':'haiku','profile':'claude-work','provider':'claude','model':'claude-haiku-5-5','effort':'medium'},
    {'id':'gemini','profile':'antigravity','provider':'antigravity','model':'gemini-3.8-flash-low','effort':'low'},
    {'id':'sol','profile':'codex-2','provider':'codex','model':'gpt-6.1-sol','effort':'medium'},
    {'id':'sonnet','profile':'claude-work','provider':'claude','model':'claude-sonnet-5-5','effort':'medium'},
]
INSTRUCTION='''You are a read-only codebase Explorer in a controlled comparison. Inspect the real source in ./repo. You are not alone on the machine; do not modify or revert any files. Use file listing, search and targeted file reads only. No source execution/imports, tests, builds, installs, network, web, delegation, git operations or account/configuration inspection. Do not inspect parent directories, other cells, original repositories or oracle/expected/experiment files. All evidence must come from the supplied repo snapshot. Native permission rules remain in force. No implementation, patch proposal or bug review is requested.
Answer EVERY numbered question by tracing the real functions, callers and branches. Distinguish similarly named lifecycle concepts, policy capabilities and actual wiring. Prefer code and tests over comments; cite tests as assertions in source, not executed results. Do not invent missing integrations or live account facts. Explicitly state material unknowns. Use repository-relative paths starting skill/scripts/, exact symbol names and inclusive line ranges. File names alone are not sufficient evidence. Cite the narrowest range that actually supports each claim. Tests may be read but never run. Do not claim any check passed.
Return ONLY one JSON object (no markdown fences), using this shape:
{"case":"E1","answers":[{"id":"Q1","answer":"concise grounded explanation","evidence":[{"path":"skill/scripts/example.py","symbol":"function_or_class","start_line":1,"end_line":8}]}],"unknowns":["material uncertainty if any"]}.
Use English. One answer per supplied question, no extra question IDs. Each answer needs at least one real code/test citation. Stay within the per-case word limit while covering every question. Do not expand into unrelated code.
TASK:
'''

def save(path,data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    tmp.replace(path)

def manifest(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

def prompt_for(case):
    limit=900 if case['difficulty']<=3 else 1600 if case['difficulty']<=5 else 2400
    return INSTRUCTION+json.dumps({**case,'maximum_whitespace_words':limit},ensure_ascii=False)

def answer_contract(text,case):
    try:obj=json.loads(text)
    except (TypeError,ValueError):return None,False
    if not isinstance(obj,dict):return obj,False
    answers=obj.get('answers');unknowns=obj.get('unknowns')
    valid=obj.get('case')==case['id'] and isinstance(answers,list) and isinstance(unknowns,list) and all(isinstance(v,str) for v in unknowns)
    expected={q['id'] for q in case['questions']}
    if not isinstance(answers,list):return obj,False
    ids=[]
    for a in answers:
        if not isinstance(a,dict):return obj,False
        ids.append(a.get('id'))
        refs=a.get('evidence')
        valid=valid and isinstance(a.get('answer'),str) and bool(a['answer'].strip()) and isinstance(refs,list) and bool(refs)
        for ref in refs if isinstance(refs,list) else []:
            valid=valid and isinstance(ref,dict) and isinstance(ref.get('path'),str) and isinstance(ref.get('symbol'),str)
            valid=valid and type(ref.get('start_line')) is int and type(ref.get('end_line')) is int and 1<=ref['start_line']<=ref['end_line']
    valid=valid and len(ids)==len(expected) and set(ids)==expected
    limit=900 if case['difficulty']<=3 else 1600 if case['difficulty']<=5 else 2400
    return obj,bool(valid and len(text.split())<=limit)

def audit(provider,stdout):
    calls=[];event_shapes={};per_message_usage=[];native_result_status=None;native_costs={}
    for line in stdout.splitlines():
        try:e=json.loads(line)
        except ValueError:continue
        if not isinstance(e,dict):continue
        et=e.get('type') or e.get('event') or 'unknown'
        event_shapes[str(et)]=sorted(e.keys())
        if provider=='claude':
            msg=e.get('message',{})
            if isinstance(msg,dict):
                if isinstance(msg.get('usage'),dict):per_message_usage.append(base.numeric_fields(msg['usage']))
                for b in msg.get('content',[]):
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        v=b.get('input',{});calls.append({'tool':b.get('name'),'input':{k:str(v[k])[:500] for k in ('file_path','path','pattern','glob') if k in v}})
            if e.get('type')=='result':native_costs=base.numeric_fields(e.get('modelUsage',{}))
        elif provider=='codex':
            item=e.get('item',{})
            if isinstance(item,dict) and e.get('type')=='item.completed' and item.get('type') in ('command_execution','mcp_tool_call','web_search'):
                calls.append({'tool':item['type'],'command':str(item.get('command',''))[:4000],'command_truncated':len(str(item.get('command','')))>4000,'exit_code':item.get('exit_code')})
        else:
            if et=='result':native_result_status=e.get('result',{}).get('status')
            if str(et) in ('tool_call','tool_use','tool_execution','tool_result'):
                calls.append({'tool':str(e.get('name') or e.get('tool_name') or e.get('tool') or et)[:160],
                              'event':et,'keys':sorted(e.keys())})
    return {'tool_audit':calls,'event_shapes':event_shapes,'per_message_usage':per_message_usage,
            'model_usage_reported':native_costs,'native_result_status':native_result_status}

def run_one(case,route):
    key=case['id']+'-'+route['id'];key += '-a2' if case['id']=='E1' else '';path=ROOT/(key+'.json')
    assert not path.exists(),f'Never repeat cell {key}'
    cwd=WORK/'cells'/case['id']/route['id'];before_files=manifest(cwd/'repo')
    expected=json.loads((ROOT/'source-hashes.json').read_text())
    assert before_files==expected,'Source mismatch before call'
    prompt=prompt_for(case)
    before=base.quota(route['profile'],route['provider'])
    record={'schema_version':1,'case':case['id'],'route':route,'status':'prepared','prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
            'prompt_characters':len(prompt),'quota_before':before,'deadline_seconds':DEADLINE,'started_at':time.time()}
    if any(v.get('used_percent',0)>=100 for k,v in before.get('windows',{}).items() if k in ('five_hour','seven_day')):
        record['status']='quota_exhausted';save(path,record);print('BLOCKED',key,'quota_exhausted',flush=True);return False
    env={k:v for k,v in os.environ.items() if k not in ('CLAUDECODE','CLAUDE_CONFIG_DIR','CODEX_HOME')}
    env.update(base.bt_profiles.env_of(route['profile']))
    provider=route['provider'];model=route['model'];effort=route['effort']
    if provider=='codex':
        args=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--model',model,
              '-c',f'model_reasoning_effort="{effort}"','-c','web_search="disabled"','--json','-'];stdin=prompt
    elif provider=='claude':
        args=['claude','--print','--model',model,'--effort',effort,'--safe-mode','--restricted','--tools','Read,Grep,Glob',
              '--allowedTools','Read,Grep,Glob','--no-session-persistence','--permission-mode','plan','--output-format','stream-json','--verbose'];stdin=prompt
    else:
        args=['agy','--model',model,'--effort',effort,'--mode','plan','--sandbox','--disable-slash-commands',
              '--output-format','stream-json','--print-timeout',f'{DEADLINE}s','--print='+prompt];stdin=None
    record.update(status='running',argv=[a if not a.startswith('--print=') else '--print=<shared hashed prompt>' for a in args]);save(path,record)
    print('START',key,route['profile'],effort,flush=True);started=time.monotonic()
    p=subprocess.Popen(args,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       text=True,cwd=cwd,env=env,start_new_session=True)
    timed_out=False
    try:stdout,stderr=p.communicate(input=stdin,timeout=DEADLINE+30)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
    parsed=base.extract(provider,stdout);obj,valid=answer_contract(parsed['response_text'],case)
    record.update(parsed)
    record.update(answer=obj,format_valid=valid,response_words=len(parsed['response_text'].split()),
                  exit_code=p.returncode,status='timeout' if timed_out else 'completed' if p.returncode==0 else 'cli_error',
                  elapsed_seconds=round(time.monotonic()-started,3),finished_at=time.time())
    save(path,record)  # Preserve final answer/usage before optional audit processing.
    record.update(audit(provider,stdout))
    if timed_out and not parsed['usage_reported']:record['usage_reported']=None
    if provider=='claude' and record['observed_models'] and record['observed_models']!=[model]:record['status']='model_identity_mismatch'
    if provider=='antigravity' and record.get('native_result_status') not in (None,'SUCCESS','success') and record['status']=='completed':record['status']='provider_error'
    if record['status']!='completed':record['error_flags']={s:s in stderr.lower() for s in ('quota','limit','permission','auth','timeout','model','sandbox')}
    after_files=manifest(cwd/'repo');record['workspace_changes']=[k for k in set(before_files)|set(after_files) if before_files.get(k)!=after_files.get(k)]
    record['quota_after']=base.quota(route['profile'],provider);save(path,record)
    print('DONE',key,record['status'],record['elapsed_seconds'],'s','JSON',valid,'tools',len(record['tool_audit']),'changes',len(record['workspace_changes']),flush=True)
    return record['status'] not in ('quota_exhausted','model_identity_mismatch') and not record['workspace_changes']

def lane(provider,cases):
    own=[r for r in ROUTES if r['provider']==provider]
    for i,c in enumerate(cases):
        schedule=[r for r in own if c['difficulty']>=4 or r['id'] in ('luna','haiku','gemini')]
        if i%2:schedule.reverse()
        for r in schedule:
            if not run_one(c,r):return {'provider':provider,'status':'stopped','case':c['id'],'route':r['id']}
    return {'provider':provider,'status':'complete'}

if __name__=='__main__':
    assert (ROOT/'protocol.json').exists() and not (ROOT/'protocol-recovery.json').exists(),'Exactly one declared collector repair'
    cases=json.loads((ROOT/'cases.json').read_text())
    frozen={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('cases.json','oracle.json','source-hashes.json','setup.py','run.py')}
    frozen['base_harness']=hashlib.sha256(BASE.read_bytes()).hexdigest()
    save(ROOT/'protocol-recovery.json',{'schema_version':1,'scope':'Owner-authorized real-source Explorer pilot, outside formal REQ-024 benchmark',
        'recovery':'Initial three E1 calls returned but a collector dict.update TypeError discarded final data. Original records preserved/excluded; exactly three replacement E1 calls use -a2. No model failure or zero consumption inferred. Original protocol retained; corrected runner hash pinned here. Maximum 27 native attempts for 24 measured cells.',
        'target_calls':24,'cases':6,'criteria':40,'routes':ROUTES,'deadline_seconds':DEADLINE,'instruction':INSTRUCTION,'frozen_hashes':frozen,
        'concurrency':'Three providers in parallel, one call per account. Codex-2 serves both Luna and Sol serially; Claude Work serves Haiku/Sonnet serially. Pair order alternates by case.',
        'grading':'Frozen per-question source-backed oracle; coordinator adjudication and structural/file/line checks; no independent model reviewer or repair calls.',
        'limitations':['One repetition per cell; no statistical superiority inference.','Source snapshot includes local uncommitted implementation; no live credentials or state.',
                      'Native tools/context/cache differ. Model effort labels are not equivalent compute budgets.','Unknown and delayed account quotas remain unknown; no API-to-subscription conversion.',
                      'Codex requested model/effort and AGY low variant are pinned; effective runtime identity attestation may be unavailable.','Native read-only modes and instructions differ; before/after hashes prove net source state only.']})
    versions={}
    for binary in ('codex','claude','agy'):
        v=subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=15)
        versions[binary]={'exit_code':v.returncode,'version':(v.stdout or v.stderr).strip()[:250]}
    save(ROOT/'runtime-versions.json',versions)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(lambda provider:lane(provider,cases),('codex','claude','antigravity')))
    save(ROOT/'execution-summary.json',results);print('EXECUTION SUMMARY',json.dumps(results),flush=True)
