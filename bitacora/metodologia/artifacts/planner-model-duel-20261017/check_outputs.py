"""Host-side frozen validator; records genuine first-response failures without repair."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORK=Path(json.loads((ROOT/'workspace.json').read_text())['root'])
results=[]
for path in sorted(ROOT.glob('CP[123]-*.json')):
 if '-files-' in path.name:continue
 r=json.loads(path.read_text())
 if r['status'] in ('running','prepared'):continue
 key=path.stem;out=ROOT/'outputs'/key;cell={'record':path.name,'status':r['status'],'block_contract_valid':r.get('block_contract_valid',False),'checks':{}}
 if not (out/'PLAN.json').exists() or not (out/'PLAN.md').exists():
  cell['checks']['capture']={'exit_code':None,'error':'Missing captured PLAN.md/PLAN.json; no repair performed'};results.append(cell);continue
 env=dict(os.environ,PYTHONPATH=str(ROOT/'validator'),PYTHONDONTWRITEBYTECODE='1')
 for action in ('validate','check','report'):
  target=out/'PLAN.json' if action=='validate' else out
  args=[sys.executable,'-m','bt_planner',action,str(target),'--plan-id',f"REQ-{r['case']}"]
  if action!='report':args+=['--json']
  if action=='check':args+=['--repo','repository='+str(WORK/r['case']/r['route']['id']/'repo')]
  p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=30)
  data={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  try:data['result']=json.loads(p.stdout)
  except ValueError:pass
  cell['checks'][action]=data
 results.append(cell)
(ROOT/'deterministic-checks.json').write_text(json.dumps(results,indent=2)+'\n')
for x in results:print(x['record'],x['block_contract_valid'],{k:v['exit_code'] for k,v in x['checks'].items()})
