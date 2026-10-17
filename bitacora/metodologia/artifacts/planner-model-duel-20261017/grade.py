"""Unblind saved semantic judgements and join immutable first-response checks."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
judgements=json.loads((ROOT/'blind-judgements.json').read_text())
views={v['blind_id']:v for v in json.loads((ROOT/'blind-plans.json').read_text())}
assert len(views)==9 and set(judgements)==set(views),'Save all nine route-hidden judgements first'
# Read the route key only after the judgements are complete.
key=json.loads((ROOT/'blind-key.json').read_text())
cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
checks={Path(c['record']).stem:c for c in json.loads((ROOT/'deterministic-checks.json').read_text())}
metrics={Path(c['record']).stem:c for c in json.loads((ROOT/'metrics.json').read_text())['records']}
cells=[]
for ident,j in judgements.items():
 name=key[ident];m=metrics[name];expected=cases[m['case']]['oracle'];items=j['items']
 assert len(items)==len(expected) and {x['id'] for x in items}=={x['id'] for x in expected}
 assert all(x['status'] in ('full','partial','missing') and x.get('evidence') for x in items)
 cell={'blind_id':ident,'record':name+'.json','case':m['case'],'route':m['route'],'status':m['status'],'oracle_items':items,'notes':j.get('notes',[]),'tool_calls':m['tool_calls'],'block_contract_valid':m['block_contract_valid'],'elapsed_seconds':m['elapsed_seconds'],'usage':m['usage'],'checks':checks[name]['checks']}
 cell['full']=sum(x['status']=='full' for x in items);cell['partial']=sum(x['status']=='partial' for x in items);cell['missing']=sum(x['status']=='missing' for x in items)
 cells.append(cell)
summaries=[]
for route in ('opus','sol','astra'):
 group=[c for c in cells if c['route']['id']==route];assert len(group)==3
 summaries.append({'route':group[0]['route'],'full':sum(c['full'] for c in group),'partial':sum(c['partial'] for c in group),'missing':sum(c['missing'] for c in group),'items':13,
 'valid_output_blocks':sum(bool(c['block_contract_valid']) for c in group),'schema_valid':sum(c['checks'].get('validate',{}).get('exit_code')==0 for c in group),'publishable_first_response':sum(c['checks'].get('check',{}).get('exit_code')==0 for c in group)})
result={'schema_version':1,'method':'Coordinator semantic judgement on shuffled route-hidden drafts, case by case; metadata diagnostics and writing style can reveal identity. No independent reviewer pair or numeric intelligence score. Candidate oracle behaviors checked against actual source; source-path hints are not authoritative golden solutions.','cells':cells,'summaries':summaries}
(ROOT/'adjudication.json').write_text(json.dumps(result,indent=2)+'\n')
for s in summaries:print(s['route']['id'],'semantic full/partial/missing',s['full'],s['partial'],s['missing'],'publishable',s['publishable_first_response'],'of3')
