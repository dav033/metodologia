"""Create a model/effort-hidden grading view after execution; unblind last."""
import json,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parent
paths=sorted(ROOT.glob('E*-*.json'))
assert len(paths)==12 and all(json.loads(p.read_text())['status']!='running' for p in paths)
assert not (ROOT/'blind-key.json').exists(), 'Do not reshuffle grading identities'
secrets.SystemRandom().shuffle(paths)
key={};views=[]
for i,p in enumerate(paths,1):
 d=json.loads(p.read_text());ident=f'B{i:02d}';key[ident]=p.stem
 views.append({'blind_id':ident,'case':d['case'],'answer':d.get('answer'),'format_valid':d.get('format_valid'),'status':d['status']})
(ROOT/'blind-key.json').write_text(json.dumps(key,indent=2)+'\n')
(ROOT/'blind-answers.json').write_text(json.dumps(views,indent=2)+'\n')
print('12 blinded views created; mapping saved separately. Grade before reading key.')
