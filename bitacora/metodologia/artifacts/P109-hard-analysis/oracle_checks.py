"""Check concrete witnesses before any model is shown the three dossiers."""
from decimal import Decimal as D, ROUND_HALF_EVEN, ROUND_HALF_UP
import hashlib
import itertools
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
checks = {}
key = lambda tenant, invoice: hashlib.sha256((tenant + ':' + invoice).encode()).hexdigest()
checks['H1-D1'] = key('a:b','c') == key('a','b:c')
checks['H1-D2'] = 100 + sum(v for rev,v in [(40,20),(41,5)] if rev>=40) != 100 + sum(v for rev,v in [(40,20),(41,5)] if rev>40)
checks['H1-D3'] = (D(100)/D('1.10')).quantize(D('.01')) != (D(100)/D('1.25')).quantize(D('.01'))
checks['H1-D4'] = D('1.005').quantize(D('.01'),rounding=ROUND_HALF_EVEN) != D('1.005').quantize(D('.01'),rounding=ROUND_HALF_UP)
checks['H1-D5'] = [r for r in [('A','INV7'),('B','INV7')] if r[1]=='INV7'] == [('A','INV7'),('B','INV7')]
state={'ledger_revision':10,'balance_v2':100,'source_revision_v2':10,'migration_epoch':None}
backfill=dict(state);state.update(ledger_revision=11,balance_v2=120,source_revision_v2=11)
if state['migration_epoch'] is None:state.update(balance_v2=backfill['balance_v2'],source_revision_v2=backfill['ledger_revision'],migration_epoch=1)
checks['H1-D6'] = state['ledger_revision']==11 and state['source_revision_v2']==10 and state['balance_v2']==100
required={'p0':90,'p1':10}; applied={'p0':89,'p1':100}
checks['H1-D7'] = sum(applied.values()) >= sum(required.values()) and not all(applied[p]>=n for p,n in required.items())
checks['H1-D8'] = 10*86400 > 7*86400  # stable key can be forgotten by the allowed provider

matrix={'J1':{'A':1,'B':2},'J2':{'A':1}}
capacity={'A':1,'B':1}; greedy={}
for task,candidates in matrix.items():
    eligible=[a for a in candidates if capacity[a]]
    if eligible:
        a=min(eligible,key=lambda a:(candidates[a],a));greedy[task]=a;capacity[a]-=1
feasible=[pair for pair in itertools.product(matrix['J1'],matrix['J2']) if len(set(pair))==2]
checks['H2-D1'] = len(greedy)==1 and ('B','A') in feasible
checks['H2-D2'] = 900<=1000<=1020 and not 900<=1100<=1020
checks['H2-D3'] = 1000*20+800*2==21600 and (1000-800)*20+800*2==5600
checks['H2-D4'] = 'run:task:1' != 'run:task:2'  # correct local CAS cannot merge distinct external keys
checks['H2-D5'] = 20 < 21 < 22  # checked, ACKed, then externally started: violates the declared ACK contract
checks['H2-D6'] = hashlib.sha256(b'/cache/quotas.json').digest()==hashlib.sha256(b'/cache/quotas.json').digest() and {'used':10}!={'used':90}
checks['H2-D7'] = 60+5 < 90 and 80+60 > 90
checks['H2-D8'] = 10+25 != 25

def cached_read(cached,grant):
    if cached:return 'data'
    if not grant:return 'denied'
    return 'data'
checks['H3-D1'] = cached_read(True,False)=='data' and cached_read(False,False)=='denied'
old=hashlib.sha256(b'approved-query').hexdigest();new=hashlib.sha256(b'broadened-query').hexdigest()
checks['H3-D2'] = old=={'client_hash':old,'actual_query_hash':new}['client_hash'] and old!=new
def sql_predicate(tenant_ok,ts,ident):return (tenant_ok and ts>10) or (ts==10 and ident>100)
checks['H3-D3'] = sql_predicate(False,10,101)
prefix=b'12345678';nonce=lambda index:prefix+index.to_bytes(4,'big')
checks['H3-D4'] = nonce(0)==nonce(0) and b'old-content'!=b'new-content'
H=lambda b:hashlib.sha256(b).digest()
def merkle(digests):
    nodes=[H(b'leaf'+d) for d in digests]
    while len(nodes)>1:
        if len(nodes)%2:nodes.append(nodes[-1])
        nodes=[H(b'node'+nodes[i]+nodes[i+1]) for i in range(0,len(nodes),2)]
    return nodes[0]
digests=[H(x) for x in [b'a',b'b',b'c']]
checks['H3-D5'] = merkle(digests)==merkle(digests+[digests[-1]])
checks['H3-D6'] = PurePosixPath('/selected/current/file.csv').is_relative_to('/selected') and not PurePosixPath('/outside/file.csv').is_relative_to('/selected')
checks['H3-D7'] = 7+24 > 24 and 7 < 8
cell='\t=1+1';guarded="'"+cell if cell[0] in '=+-@' else cell
checks['H3-D8'] = guarded.lstrip(' \t\r').startswith('=')
assert len(checks)==24 and all(checks.values()), checks
cases=json.loads((ROOT/'cases.json').read_text())
assert {d['id'] for c in cases for d in c['oracle']}==set(checks)
result={'oracle_sha256':hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest(),
        'checks':checks,'passed':24,'method':'Executable arithmetic/logic witnesses plus explicitly modeled lifecycle traces; not production integration tests.'}
(ROOT/'oracle-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('24/24 predeclared counterexample checks passed; oracle hash',result['oracle_sha256'])
