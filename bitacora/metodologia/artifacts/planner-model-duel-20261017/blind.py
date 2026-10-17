"""Append a completed case's shuffled route-hidden plans; never relabel earlier cases."""
import json,secrets,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
case=sys.argv[1]
assert case in ('CP1','CP2','CP3')
key_path=ROOT/'blind-key.json';view_path=ROOT/'blind-plans.json'
key=json.loads(key_path.read_text()) if key_path.exists() else {}
views=json.loads(view_path.read_text()) if view_path.exists() else []
assert not any(v['case']==case for v in views),'Do not reshuffle existing case'
paths=[p for p in sorted(ROOT.glob(case+'-*.json')) if '-files-' not in p.name]
assert len(paths)==3 and all(json.loads(p.read_text())['status'] not in ('prepared','running') for p in paths)
secrets.SystemRandom().shuffle(paths)
for p in paths:
 r=json.loads(p.read_text());label=f'P{len(key)+1:02d}';key[label]=p.stem;output=ROOT/'outputs'/p.stem
 md=(output/'PLAN.md').read_text() if (output/'PLAN.md').exists() else ''
 views.append({'blind_id':label,'case':r['case'],'status':r['status'],'markdown':md,'plan':r.get('plan'),'block_contract_valid':r.get('block_contract_valid',False)})
key_path.write_text(json.dumps(key,indent=2)+'\n');view_path.write_text(json.dumps(views,indent=2)+'\n')
print(case,'three route-hidden views appended; key saved separately, not displayed.')
