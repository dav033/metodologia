"""Nine owner-authorized native Planner calls on matched immutable source copies."""
import concurrent.futures,hashlib,importlib.util,json,os,re,shutil,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'P109-review-ladder/run.py'
spec=importlib.util.spec_from_file_location('pilot_collectors',BASE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
WORK=Path(json.loads((ROOT/'workspace.json').read_text())['root'])
DEADLINE=900
ROUTES=[{'id':'opus','profile':'claude-work','provider':'claude','model':'claude-opus-5-5','effort':'high'},
        {'id':'sol','profile':'codex-2','provider':'codex','model':'gpt-6.1-sol','effort':'high'},
        {'id':'astra','profile':'codex-2','provider':'codex','model':'gpt-6-astra','effort':'high'}]
TASK='''Controlled source-backed planning comparison. The complete shared Planner role/private skills/references are included below. Follow them to draft, not implement.
Work only inside this isolated cell. The repository mapping is `repository` -> `./repo`; the requirement is `./request/SPEC.md`; schema and a generic example are in `./planner-resources/`. Inspect the requirement AND actual affected code/consumers/tests/configuration using read-only tools. The example teaches shape only, never task scope. Do not inspect other cells, oracle/expected files, original repositories, account configuration or private home files. No web, delegation, subagents, installs, git mutations, tests, builds or other executed code. Codex may use read-only shell commands to list/search/read files; Claude has Read/Grep/Glob only. Do not modify any file. The host captures outputs and runs frozen deterministic validation/check/report afterwards; do not claim any command passed or run the validator yourself.
Return a reviewable DRAFT even when the supplied requirement leaves product choices open: explicitly retain unknowns, proposed assumptions and decision-gated tasks. Do not invent owner approval, external consumer compatibility, executed commands or measured estimates. No actual owner Q&A occurs in this experiment. Do not approve/freeze/launch anything or assign providers/models/accounts/efforts/workers. No more than 8 independently actionable tasks. Aim for concise actionable plans rather than verbosity; completeness, safe dependencies and evidence matter.
Return exactly TWO fenced blocks with filename language labels, no other text:
```PLAN.md
<draft plan with scope, inspected findings and provenance, numbered milestone headings and checkbox task lines consistent with JSON, risks/assumptions/decision gates, task behavior, acceptance and verification>
```
```PLAN.json
<one complete valid schema_version 1.2.0 object, revision 1, spec_ref SPEC.md, repository keys repository, real R1/R2/R3 coverage, all classifications/evidence and any necessary interfaces>
```
No diagram. File evidence must be repository-relative (such as apps/api/src/app.ts), not prefixed repo/. Planned new tests are not existing evidence; specify created_by where appropriate. Estimates remain estimates; no comparable execution history is available in this sandbox. Use English. Per-case plan_id follows below.

SHARED PLANNER INSTRUCTIONS:
'''
def save(path,data):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)
def tree_manifest(root):
 result={}
 for p in sorted(root.rglob('*')):
  if p.is_symlink():result[str(p.relative_to(root))]={'symlink':os.readlink(p)}
  elif p.is_file():result[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return result
def parse_blocks(text):
 blocks=re.findall(r'^```([^\n]*)\n(.*?)^```[ \t]*$',text,re.M|re.S)
 out={};valid=len(blocks)==2
 for label,body in blocks:
  label=label.strip()
  if label not in ('PLAN.md','PLAN.json') or label in out:valid=False
  out[label]=body.rstrip()+'\n'
 residual=re.sub(r'^```[^\n]*\n.*?^```[ \t]*$','',text,flags=re.M|re.S).strip()
 valid=valid and not residual and set(out)=={'PLAN.md','PLAN.json'}
 obj=None
 if 'PLAN.json' in out:
  try:obj=json.loads(out['PLAN.json'])
  except ValueError:valid=False
 return out,obj,bool(valid and isinstance(obj,dict))
def audit_events(provider,stdout):
 calls=[];models=set();aggregate_by_model={}
 for line in stdout.splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  if not isinstance(e,dict):continue
  if provider=='claude':
   msg=e.get('message',{})
   if isinstance(msg,dict):
    if isinstance(msg.get('model'),str):models.add(msg['model'])
    for b in msg.get('content',[]):
     if isinstance(b,dict) and b.get('type')=='tool_use':
      v=b.get('input',{});calls.append({'tool':b.get('name'),'input':{k:str(v[k])[:400] for k in ('file_path','path','pattern','glob') if k in v}})
   if e.get('type')=='result':aggregate_by_model=base.numeric_fields(e.get('modelUsage',{}))
  else:
   item=e.get('item',{})
   if isinstance(item,dict) and e.get('type')=='item.completed' and item.get('type') in ('command_execution','mcp_tool_call','web_search'):
    calls.append({'tool':item['type'],'command':str(item.get('command',''))[:1200],'exit_code':item.get('exit_code')})
 return {'tool_audit':calls,'model_usage_reported':aggregate_by_model}
def run_one(c,r):
 key=c['id']+'-'+r['id'];record_path=ROOT/(key+'.json')
 if record_path.exists():
  old=json.loads(record_path.read_text());print('EXISTS',key,old['status'],flush=True);return old['status']=='completed'
 cwd=WORK/c['id']/r['id'];prompt=TASK+(ROOT/'planner-instructions.md').read_text()+'\n\nCASE PLAN ID: '+c['plan_id']+'\n'
 before=base.quota(r['profile'],r['provider']);record={'schema_version':1,'case':c['id'],'route':r,'status':'prepared','prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'prompt_characters':len(prompt),'quota_before':before,'deadline_seconds':DEADLINE,'started_at':time.time()}
 if any(v.get('used_percent',0)>=100 for k,v in before.get('windows',{}).items() if k in ('five_hour','seven_day')):
  record['status']='quota_exhausted';save(record_path,record);return False
 before_files=tree_manifest(cwd);save(ROOT/(key+'-files-before.json'),before_files)
 env={k:v for k,v in os.environ.items() if k not in ('CLAUDECODE','CLAUDE_CONFIG_DIR','CODEX_HOME')};env.update(base.bt_profiles.env_of(r['profile']))
 if r['provider']=='codex':
  args=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--model',r['model'],'-c','model_reasoning_effort="high"','-c','web_search="disabled"','--json','-']
 else:
  args=['claude','--print','--model',r['model'],'--effort','high','--safe-mode','--restricted','--tools','Read,Grep,Glob','--allowedTools','Read,Grep,Glob','--no-session-persistence','--permission-mode','plan','--output-format','stream-json','--verbose']
 record.update(status='running',argv=args);save(record_path,record);print('START',key,flush=True);started=time.monotonic()
 try:
  result=subprocess.run(args,input=prompt,text=True,capture_output=True,cwd=cwd,env=env,timeout=DEADLINE+30)
  parsed=base.extract(r['provider'],result.stdout);blocks,plan,valid=parse_blocks(parsed['response_text']);record.update(parsed)
  record.update(audit_events(r['provider'],result.stdout),status='completed' if result.returncode==0 else 'cli_error',exit_code=result.returncode,block_contract_valid=valid,plan=plan)
  output=ROOT/'outputs'/key;output.mkdir(parents=True,exist_ok=True)
  for name,body in blocks.items():
   if name in ('PLAN.md','PLAN.json'):(output/name).write_text(body)
  (output/'SPEC.md').write_text(c['spec'])
  if result.returncode!=0:record['error_excerpt']=result.stderr[-1500:]
  if r['provider']=='claude' and parsed['observed_models']!=[r['model']]:record['status']='model_identity_mismatch'
 except subprocess.TimeoutExpired:
  record.update(status='timeout',exit_code=None,usage_reported=None,block_contract_valid=False)
 record['elapsed_seconds']=round(time.monotonic()-started,3)
 after_files=tree_manifest(cwd);changes=[k for k in sorted(set(before_files)|set(after_files)) if before_files.get(k)!=after_files.get(k)];record['workspace_changes']=changes
 record['quota_after']=base.quota(r['profile'],r['provider']);save(record_path,record)
 print('DONE',key,record['status'],record['elapsed_seconds'],'s','blocks',record.get('block_contract_valid'),'tools',len(record.get('tool_audit',[])),'changed',changes,flush=True)
 return record['status']=='completed' and not changes
def lane(provider,cases):
 if provider=='claude':schedule=[(c,ROUTES[0]) for c in cases]
 else:schedule=[(c,r) for i,c in enumerate(cases) for r in ([ROUTES[1],ROUTES[2]] if i%2==0 else [ROUTES[2],ROUTES[1]])]
 for c,r in schedule:
  if not run_one(c,r):return {'provider':provider,'status':'stopped','case':c['id'],'route':r['id']}
 return {'provider':provider,'status':'complete'}
if __name__=='__main__':
 cases=json.loads((ROOT/'cases.json').read_text());sources=json.loads((ROOT/'source-hashes.json').read_text())
 assert hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest()==sources['cases_sha256']
 assert hashlib.sha256((ROOT/'planner-instructions.md').read_bytes()).hexdigest()==sources['planner_bundle_sha256']
 protocol={'schema_version':1,'scope':'Owner-authorized source-backed Planner model pilot; separate from formal REQ-024 matched-arm benchmark','routes':ROUTES,'target_calls':9,'cases_sha256':sources['cases_sha256'],'planner_bundle_sha256':sources['planner_bundle_sha256'],'task_instruction':TASK,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_harness_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'deadline_seconds':DEADLINE,'maximum_tasks':8,'output':'Two filename-labeled PLAN.md/PLAN.json fenced blocks, schema1.2.0','concurrency':'One call per account; Claude and Codex lanes parallel; Sol/Astra order alternates by case','corpus':'Pinned existing C2/C3/C4 source/spec/oracle candidate copies; no formal manifest or quality score modified','grading':'Frozen deterministic validator plus route-hidden coordinator semantic rubric; no new independent model-review calls. No automatic retries, repairs or fallback.'}
 assert not (ROOT/'protocol.json').exists(),'Do not silently restart the pilot'
 save(ROOT/'protocol.json',protocol)
 versions={}
 for executable in ('codex','claude'):
  v=subprocess.run([executable,'--version'],capture_output=True,text=True,timeout=15);versions[executable]={'exit_code':v.returncode,'version':(v.stdout or v.stderr).strip()[:200]}
 save(ROOT/'runtime-versions.json',versions)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda provider:lane(provider,cases),('claude','codex')))
 save(ROOT/'execution-summary.json',results);print('EXECUTION SUMMARY',json.dumps(results),flush=True)
