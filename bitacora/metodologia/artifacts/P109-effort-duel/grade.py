"""Unblind only after the coordinator has saved route-hidden adjudication."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
protocol=json.loads((ROOT/'protocol.json').read_text())
cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
assert hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest()==protocol['oracle_sha256']
judgements=json.loads((ROOT/'blind-judgements.json').read_text())
views={v['blind_id']:v for v in json.loads((ROOT/'blind-answers.json').read_text())}
assert set(judgements)==set(views)
key=json.loads((ROOT/'blind-key.json').read_text())
def usage(record):
    u=record.get('usage_reported')
    if not isinstance(u,dict) or 'input_tokens' not in u:return None
    if record['route']['provider']=='claude':
        inp=sum(u.get(k,0) for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens'))
        cached=u.get('cache_read_input_tokens',0);thinking=u.get('output_tokens_details',{}).get('thinking_tokens')
    else:
        inp=u['input_tokens'];cached=u.get('cached_input_tokens',0);thinking=u.get('reasoning_output_tokens')
    out=u.get('output_tokens')
    return {'input_including_cache':inp,'cached_read_subset':cached,'output_including_thinking':out,'thinking_subset':thinking,'total_tokens':inp+out}
cells=[]
for blind,j in judgements.items():
    r=json.loads((ROOT/(key[blind]+'.json')).read_text());case=cases[r['case']]
    assert r['prompt_sha256']==hashlib.sha256((protocol['instruction']+case['input']).encode()).hexdigest()
    mapping=j['mapping'];answer=r.get('answer')
    assert isinstance(answer,dict) and len(mapping)==len(answer['findings'])
    found=set();extra=[]
    for index,item in enumerate(mapping,1):
        if isinstance(item,int):found.add(f"{r['case']}-D{item}")
        elif isinstance(item,list):found.update(f"{r['case']}-D{i}" for i in item)
        elif isinstance(item,str):extra.append({'finding':index,'extra':item})
    expected={v['id'] for v in case['oracle']};assert found<=expected
    cells.append({'record':key[blind]+'.json','blind_id':blind,'case':r['case'],'route':r['route'],'status':r['status'],
                  'finding_map':mapping,'seeded_found':sorted(found),'seeded_expected':len(expected),'seeded_missed':sorted(expected-found),
                  'extras':extra,'notes':j.get('notes',[]),'format_valid':r['format_valid'],'elapsed_seconds':r['elapsed_seconds'],'usage':usage(r)})
summaries=[]
for route in protocol['routes']:
    group=sorted([c for c in cells if c['route']['id']==route['id']],key=lambda c:c['case']);assert len(group)==3
    totals={k:sum(c['usage'][k] for c in group) if all(c['usage'] is not None and c['usage'][k] is not None for c in group) else None for k in group[0]['usage']}
    summaries.append({'route':route,'seeded_found':sum(len(c['seeded_found']) for c in group),'seeded_expected':31,
                     'valid_json':sum(c['format_valid'] for c in group),'elapsed_seconds':round(sum(c['elapsed_seconds'] for c in group),3),
                     'usage':totals,'notes':sum(len(c['notes']) for c in group)})
result={'schema_version':1,'oracle_sha256':protocol['oracle_sha256'],'method':'Coordinator mapped route-hidden shuffled answers before this unblinding; style can still identify models. Single run per cell; no statistical ranking.',
        'cells':cells,'summaries':summaries,'limitations':['Seeded recall does not guarantee every fix is sound; notes preserve counterexamples and conditional extras.','Effort is explicitly requested, not independently attested by final metadata.','Quota is account-level, rounded and lagged; interleaved efforts prevent exact effort-level attribution.']}
(ROOT/'adjudication.json').write_text(json.dumps(result,indent=2)+'\n')
for s in summaries:print(s['route']['id'],s['seeded_found'],s['usage'],s['elapsed_seconds'],'valid',s['valid_json'])
