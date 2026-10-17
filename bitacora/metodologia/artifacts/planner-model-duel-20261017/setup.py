"""Prepare immutable source-backed Planner comparison inputs, without inference."""
import hashlib,json,shutil,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
# ROOT is <repo>/bitacora/metodologia/artifacts/<name>.
assert (REPO/'skill').is_dir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT.parent/'REQ-024-benchmark-config-candidates/claude-opus-5-5-high/paired-readonly/arms/improved-v2'
hashes=json.loads((source/'candidate-hashes.json').read_text())
for item in hashes['sources']:assert sha(REPO/item['path'])==item['sha256'],item['path']
assert sha(source/'prompt-bundle.md')==hashes['prompt_bundle_sha256']
shutil.copyfile(source/'prompt-bundle.md',ROOT/'planner-instructions.md')
shutil.copyfile(REPO/'skill/scripts/bt_planner/data/plan.schema.json',ROOT/'plan.schema.json')
shutil.copyfile(REPO/'skill/scripts/bt_planner/data/plan.example.json',ROOT/'plan.example.json')
case_defs=[('CP1','C2','TRAIN-3-project-list-contract'),('CP2','C3','TRAIN-6-postgres-migration'),('CP3','C4','METH-4-plan-quality-in-review')]
cases=[]
for ident,corpus,scenario in case_defs:
 archive=ROOT.parent/f'REQ-024-benchmark/corpus-candidates/{corpus}-source.tar'
 spec=REPO/f'skill/scripts/bt_planner/tests/scenarios/{scenario}/SPEC.md'
 oracle=ROOT.parent/f'REQ-024-benchmark/oracle-candidates/{corpus}.json'
 cases.append({'id':ident,'plan_id':f'REQ-{ident}','corpus_source':corpus,'archive':str(archive),'archive_sha256':sha(archive),'spec':spec.read_text(),'spec_sha256':sha(spec),'oracle':json.loads(oracle.read_text())['items']})
(ROOT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
# Preserve source archives; per-cell copies live outside the project tree.
workspace=Path(tempfile.mkdtemp(prefix='metodologia-planner-duel-20261017-'))
(ROOT/'workspace.json').write_text(json.dumps({'root':str(workspace),'retention':'Retained scratch copies; rebuild from pinned archives. No automatic deletion.'},indent=2)+'\n')
for c in cases:
 for route in ('opus','sol','astra'):
  cell=workspace/c['id']/route;repo=cell/'repo';repo.mkdir(parents=True)
  with tarfile.open(c['archive']) as t:t.extractall(repo,filter='data')
  # Canonical source snapshots already exclude target Planner scenarios and bitacora.
  assert not (repo/'skill/scripts/bt_planner/tests/scenarios').exists()
  assert not (repo/'bitacora').exists()
  request=cell/'request';request.mkdir();(request/'SPEC.md').write_text(c['spec'])
  resources=cell/'planner-resources';resources.mkdir()
  shutil.copyfile(ROOT/'plan.schema.json',resources/'plan.schema.json');shutil.copyfile(ROOT/'plan.example.json',resources/'plan.example.json')
  # Tool reads operate in an isolated copy; original source hashes are retained.
(ROOT/'source-hashes.json').write_text(json.dumps({'planner_bundle_sha256':sha(ROOT/'planner-instructions.md'),'canonical_sources':hashes['sources'],'schema_sha256':sha(ROOT/'plan.schema.json'),'cases_sha256':sha(ROOT/'cases.json')},indent=2)+'\n')
print('Prepared three pinned cases and nine isolated repository copies at',workspace)
