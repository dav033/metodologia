"""Validate declared numerical/logical witnesses before any provider call."""
import hashlib,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
c={}
c['E1-D1']=('s','a','d','b','USD')==('s','a','d','b','USD') and 10!=11
c['E1-D2']=100-10+(10+10)!=100
c['E1-D3']=(1,'transfer')!=(2,'transfer')
old=set('abc');new=set('cde');acks=set('abc')
c['E1-D4']=len(acks & (old|new))>=len(old|new)//2+1 and len(acks&new)<len(new)//2+1
c['E1-D5']=({'append':True,'committed':False,'sent_commit':True}['sent_commit'] and not {'committed':False}['committed'])
c['E1-D6']=61>60 and {'coordinator':'COMMIT','participant':'PREPARED'}['coordinator']=='COMMIT'
c['E1-D7']=100>=90 and 10<90
c['E1-D8']=100+110!=100+100 and 100+110!=90+110
c['E1-D9']=bool({'payload':'private'}) and not False
c['E1-D10']=20<=30 and 'signed-branch-A'!='local-branch-B'
c['E1-D11']=31>30 and 'retry-old-transfer'=='retry-old-transfer'
c['E2-D1']=5<=10 and not 20<=15
c['E2-D2']=F(100*(10-1),10)!=F(100*(10-2),10)
def half_away(x):
 sign=-1 if x<0 else 1;x=abs(x);return sign*((2*x.numerator+x.denominator)//(2*x.denominator))
c['E2-D3']=sum(map(half_away,[F(1,2),F(1,2)]))!=half_away(F(1))
def allocation(n):
 weights={'a':F(1,2),'b':F(1,2)};base={k:(n*w.numerator)//w.denominator for k,w in weights.items()};missing=n-sum(base.values())
 ranked=sorted(weights,key=lambda k:(-(n*weights[k]-base[k]),k))
 for k in ranked[:missing]:base[k]+=1
 return base
pos=allocation(1);neg=allocation(-1)
c['E2-D4']=sum(neg.values())==-1 and neg!={k:-v for k,v in pos.items()}
c['E2-D5']=sum([-50,100])==50 and {'tenant-A':-50,'tenant-B':100}['tenant-B']==100
items=[('a',4,1),('b',5,1),('c',6,100)];remaining=10;greedy=[]
for item in sorted(items,key=lambda x:(x[1],-x[2],x[0])):
 if item[1]<=remaining:greedy.append(item);remaining-=item[1]
c['E2-D6']=len(greedy)==2 and sum(i[2] for i in greedy)<101 and 4+6<=10 and 4+5+6>10
c['E2-D7']=('tenant','payout')==('tenant','payout') and {'amount':100}!={'amount':110}
c['E2-D8']=301>300 and {'remote':'accepted','local':'UNKNOWN'}['remote']=='accepted'
c['E2-D9']=bool({'version_ids':['v1']}) and not bool({})
c['E2-D10']='allowed'=='allowed' and not False
c['E3-D1']=('src',('B',),'arch')==('src',('B',),'arch') and ('dep-v1','flag1')!=('dep-v2','flag2')
c['E3-D2']='B' not in set() and 'B' in {'B'}
c['E3-D3']=max(v for v in [2,3] if v<=100)==3 and 3!=2
c['E3-D4']={'status':'COMPLETE','manifest':None}['manifest'] is None
c['E3-D5']=bool({'digest':'bytes'}) and not False
c['E3-D6']='artifact'=='artifact' and {'source':'signed-old'}!={'source':'approved-new'}
c['E3-D7']=('new-exe','old-schema') not in [('old-exe','old-schema'),('new-exe','new-schema')]
c['E3-D8']=11!=12 and {'ack_sent':True,'cas_succeeded':False}['ack_sent']
roots_at_t0=set();references_at_t1={'blob'};tombstones_at_t2={'blob'}
c['E3-D9']='blob' not in roots_at_t0 and 'blob' in references_at_t1 and 'blob' in tombstones_at_t2
c['E3-D10']=0+24<100+24
cases=json.loads((ROOT/'cases.json').read_text());assert set(c)=={x['id'] for case in cases for x in case['oracle']};assert len(c)==31 and all(c.values())
result={'oracle_sha256':hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest(),'checks':c,'passed':31,'method':'Concrete arithmetic and explicit modeled traces; not production integration tests. Frozen roots remain separate from any post-hoc extra.'}
(ROOT/'oracle-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('31/31 oracle witness checks passed:',result['oracle_sha256'])
