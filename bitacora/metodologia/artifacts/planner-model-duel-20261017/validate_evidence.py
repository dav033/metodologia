"""Check evidence integrity; model evaluation failures remain failures in the result."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
pr=json.loads((ROOT/'protocol.json').read_text());cases=json.loads((ROOT/'cases.json').read_text());checks={}
def check(name,value):
 assert value,name
 checks[name]=True
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check('frozen_cases',sha(ROOT/'cases.json')==pr['cases_sha256'])
check('frozen_planner_bundle',sha(ROOT/'planner-instructions.md')==pr['planner_bundle_sha256'])
check('executed_runner_hash',sha(ROOT/'run.py')==pr['runner_sha256'])
check('base_collector_hash',sha(ROOT.parent/'P109-review-ladder/run.py')==pr['base_harness_sha256'])
validator=json.loads((ROOT/'validator-hashes.json').read_text())
check('frozen_validator_16_files',len(validator)==16 and all(sha(ROOT/'validator'/k)==v for k,v in validator.items()))
records=[]
for c in cases:
 for route in pr['routes']:
  r=json.loads((ROOT/(c['id']+'-'+route['id']+'.json')).read_text());records.append(r)
  prompt=pr['task_instruction']+(ROOT/'planner-instructions.md').read_text()+'\n\nCASE PLAN ID: '+c['plan_id']+'\n'
  check('matched_prompt_'+c['id']+'_'+route['id'],r['route']==route and r['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest())
check('nine_terminal_cells',len(records)==9 and all(r['status'] not in ('prepared','running') for r in records))
check('nine_native_successes',all(r['status']=='completed' and r['exit_code']==0 for r in records))
check('no_net_workspace_changes',all(r['workspace_changes']==[] for r in records))
for c in cases:
 manifests=[json.loads((ROOT/(c['id']+'-'+r['id']+'-files-before.json')).read_text()) for r in pr['routes']]
 check('identical_initial_workspaces_'+c['id'],manifests[0]==manifests[1]==manifests[2])
claude=[r for r in records if r['route']['provider']=='claude']
check('three_opus_effective_ids',len(claude)==3 and all(r['observed_models']==['claude-opus-5-5'] for r in claude))
check('claude_tool_allowlist',all(call['tool'] in ('Read','Grep','Glob') for r in claude for call in r['tool_audit']))
check('codex_observed_tool_type_is_shell',all(call['tool']=='command_execution' for r in records if r['route']['provider']=='codex' for call in r['tool_audit']))
audit=json.loads((ROOT/'tool-scope-audit.json').read_text())
check('claude_explicit_read_paths_inside_cells',all(not row['read_paths_outside_cell'] for row in audit))
check('codex_command_audit_untruncated',all(len(command)<1200 for row in audit for command in row['commands']))
for profile in ('codex-2','claude-work'):
 group=sorted([r for r in records if r['route']['profile']==profile],key=lambda x:x['started_at'])
 check('no_native_overlap_'+profile,all(a['started_at']+a['elapsed_seconds']<=b['started_at'] for a,b in zip(group,group[1:])))
metric=json.loads((ROOT/'metrics.json').read_text())
check('usage_present_nine',len(metric['records'])==9 and all(r['usage'] is not None for r in metric['records']))
for r in metric['records']:
 u=r['usage'];assert u['cache_read_subset']<=u['input_including_cache'] and u['thinking_subset']<=u['output_including_thinking'] and u['total_tokens']==u['input_including_cache']+u['output_including_thinking']
checks['token_subsets_not_double_counted']=True
# Independent arithmetic check on first-cell cost classes, not an invoice claim.
for r in metric['records']:
 if r['record']=='CP1-opus.json':check('opus_cost_arithmetic',abs(r['usage']['illustrative_standard_api_usd']-1.114224)<1e-6)
 if r['record']=='CP1-sol.json':check('sol_cost_arithmetic',abs(r['usage']['illustrative_standard_api_usd']-0.220441)<1e-6)
by_record={r['record']:r for r in metric['records']}
check('opus_equivalents_match_native_cost_metadata',all(abs(by_record[r['case']+'-opus.json']['usage']['illustrative_standard_api_usd']-r['model_usage_reported']['claude-opus-5-5']['costUSD'])<1e-6 for r in claude))
last=max(r['started_at']+r['elapsed_seconds'] for r in records);quota=json.loads((ROOT/'quota-final.json').read_text())
check('delayed_final_quota_two_ok',len(quota)==2 and all(q['status']=='ok' and q['observed_at']-last>120 for q in quota))
check('judgements_saved_before_unblinding',(ROOT/'blind-judgements.json').stat().st_mtime<=(ROOT/'adjudication.json').stat().st_mtime)
deterministic=json.loads((ROOT/'deterministic-checks.json').read_text());check('nine_host_check_records',len(deterministic)==9)
first_response={'output_blocks_valid':sum(bool(r['block_contract_valid']) for r in records),'schema_valid':sum(r['checks'].get('validate',{}).get('exit_code')==0 for r in deterministic),'publishable':sum(r['checks'].get('check',{}).get('exit_code')==0 for r in deterministic),'cells':9}
known=[]
for r in records:
 for side in ('quota_before','quota_after'):
  if r[side]['status']!='ok':known.append({'record':r['case']+'-'+r['route']['id'],'kind':side,'status':r[side]['status']})
for r in deterministic:
 errors=r['checks'].get('check',{}).get('result',{}).get('errors',[])
 if errors:known.append({'record':r['record'],'kind':'first_response_publishability','errors':errors})
jsons=list(ROOT.rglob('*.json'));scripts=list(ROOT.rglob('*.py'))
for f in jsons:json.loads(f.read_text())
for f in scripts:ast.parse(f.read_text())
check('artifact_whitespace',all(all(l.rstrip()==l for l in f.read_text().splitlines()) for f in ROOT.iterdir() if f.suffix in ('.md','.py','.json','.log')))
result={'evidence_checks':checks,'json_parsed_before_validation_write':len(jsons),'python_ast_parsed':len(scripts),'first_response_results':first_response,'known_failures':known,'limits':['First responses only; no validation-feedback repair turn','Coordinator grading only partially blinded and not independent','Requested Codex effective identity/internal effort/service tier not independently confirmed','Before/after hashes check net contents, not transient reverted writes','No product test suite or implementation executed'],'notes':['Prototype cost calculation omitted per-million output scaling; caught immediately, corrected before reporting and checked against independent arithmetic.']}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print({'evidence_checks_passed':len(checks),'first_response_results':first_response,'json_files':len(jsons),'python_files':len(scripts),'known_failures':len(known)})
