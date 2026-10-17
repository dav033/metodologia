"""Shuffle final answers without route metadata for coordinator adjudication."""
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parent
case=sys.argv[1]
routes=['luna','haiku','gemini']+(['sol','sonnet'] if int(case[1:])>=4 else [])
paths=[ROOT/f"{case}-{route}{'-a2' if case=='E1' else ''}.json" for route in routes]
paths=[ROOT/'gemini-recovery'/p.name if route=='gemini' and (ROOT/'protocol-gemini-recovery.json').exists() else p for route,p in zip(routes,paths)]
partial='--partial' in sys.argv
assert partial or all(p.exists() for p in paths)
records=[json.loads(p.read_text()) if p.exists() else {'status':'pending'} for p in paths]
assert partial or all(r['status'] not in ('running','prepared','pending') for r in records)
permutation=list(range(len(paths)));random.Random('explorer-ladder-'+case).shuffle(permutation)
folder=ROOT/'blind';folder.mkdir(exist_ok=True)
key=[];text=[]
for i,index in enumerate(permutation):
    label=case+'-'+chr(65+i);r=records[index]
    key.append({'label':label,'record':str(paths[index].relative_to(ROOT))})
    obj=r.get('answer')
    text.append('## '+label+'\n'+json.dumps(obj if obj is not None else {'unparsed_response':r.get('response_text',''),'status':r['status']},indent=2))
(folder/(case+'.md')).write_text('\n\n'.join(text)+'\n')
(ROOT/(case+'-blind-key.json')).write_text(json.dumps(key,indent=2)+'\n')
print(folder/(case+'.md'))
