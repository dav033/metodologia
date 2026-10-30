"""Reproduce exact conflicts and verify reviewed unions in both orientations, without live refs."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/home/david/dev/metodologia/skill/scripts')
from bt_composition_adapter import GitSubprocessPort
ROOT=Path(__file__).resolve().parent
SESSION=Path('/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-120814-28ad')
REPO=Path('/home/david/dev/pictures-wt/asesor')
LIVE=Path('/home/david/bitacora/.state/durable/composition/resolutions')

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');args=ap.parse_args()
 requests=[t['resolution'] for t in json.loads((SESSION/'triggers.json').read_text()) if t.get('resolution')]
 groups={}
 for r in requests:groups.setdefault(tuple(r['commits'].values()),[]).append(r)
 out=[]
 with tempfile.TemporaryDirectory(prefix='solver-r27-replay-') as d:
  tmp=Path(d);repo=tmp/'repo.git'
  subprocess.run(['git','clone','--quiet','--shared','--bare',str(REPO),str(repo)],check=True)
  folder=tmp/'resolutions';folder.mkdir()
  assigned={r['key'] for r in requests}
  for f in LIVE.glob('*.resolved'):
   if f.stem not in assigned:shutil.copyfile(f,folder/f.name)
  if args.reviewed:
   for r in requests:shutil.copyfile(ROOT/'reviewed'/(r['key']+'.resolved'),folder/(r['key']+'.resolved'))
  port=GitSubprocessPort(repo,tmp/'ws');port.resolutions=folder;port.request_resolutions=False
  for ids,rs in groups.items():
   commits=rs[0]['commits']
   for left,right in [('ours','theirs'),('theirs','ours')]:
    merged=port.merge_tree(commits['base'],commits[left],commits[right])
    row={'commits':commits,'left':left,'right':right,'tree':merged.tree,'conflicts':list(merged.conflicts),'files':{}}
    for r in rs:
     if args.reviewed:
      expected=(ROOT/'reviewed'/(r['key']+'.resolved')).read_bytes()
      actual=git(repo,'cat-file','blob',merged.tree+':'+r['path'])
      assert r['path'] not in merged.conflicts and actual==expected,r['path']
      row['files'][r['path']]={'sha256':hashlib.sha256(actual).hexdigest(),'key':r['key']}
     else:assert r['path'] in merged.conflicts,r['path']
    out.append(row)
    print(left,right,len(rs),'reviewed paths; conflicts',len(merged.conflicts))
    if args.reviewed:
     original=next(row for row in json.loads((ROOT/'baseline-replay.json').read_text()) if row['commits']==commits and row['left']==left)
     expected=set(original['conflicts'])-{r['path'] for r in rs}
     assert set(merged.conflicts)==expected,(merged.conflicts,expected)
 (ROOT/('reviewed-replay.json' if args.reviewed else 'baseline-replay.json')).write_text(json.dumps(out,indent=2)+'\n')
 if not args.reviewed:raise AssertionError('Original immutable conflicts reproduced')

if __name__=='__main__':main()
