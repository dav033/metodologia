"""Explicit coordinator mapping; frozen seeds and post-hoc discoveries stay separate."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
protocol=json.loads((ROOT/'protocol.json').read_text())
assert hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest()==protocol['oracle_sha256']

# One item per actual finding. Lists allow one well-supported finding to cover
# several frozen roots; named extras never expand the seeded denominator.
MAPS={
    'H1-sol':[1,2,3,4,5,6,7,8],
    'H2-sol':[1,2,3,4,5,6,7,8],
    'H3-sol':[1,2,3,4,5,6,7,8],
    'H1-sonnet':[1,2,3,4,5,6,7,8],
    'H2-sonnet':[1,2,3,4,5,6,7,8],
    'H3-sonnet':[1,2,3,4,5,6,7,8],
    'H1-gemini':[1,2,3,4,5,6,7,8],
    'H2-gemini':[1,2,3,4,5,6,7,8],
    'H1-luna':[1,2,3,'precision',4,5,6,7,8],
    'H2-luna':[1,2,3,4,5,6,7,8],
    'H3-luna':[3,1,2,4,5,6,7,8],
    'H1-haiku':[5,2,3,4,'precision',1,8,6,7],
    'H2-haiku':[4,1,2,5,7,8,3,6],
    'H3-haiku':[3,4,1,2,None,5,7,6,8],
}
REVIEWS={
    'H2-sonnet':[
        {'finding':7,'category':'unsafe_alternative','root':'H2-D7',
         'note':'The primary rule correctly keeps uncertain executions reserved until remote reconciliation. The alternative of merely extending reservation expiry with the lease is insufficient if cleanup then frees capacity after a local lease expires while the remote job remains live/uncertain. Retain the primary reconciliation rule even with coupled renewal.'}],
    'H2-gemini':[
        {'finding':6,'category':'insufficient_alternative','root':'H2-D6',
         'note':'Persisting allowlisted quota observations is sound. An immutable hash alone cannot reproduce inputs whose only cache copy was overwritten; a hash alternative needs retained immutable content. The dossier explicitly requires input evidence, so this is not merely an unspecified downstream preference.'},
        {'finding':7,'category':'unsafe_main_fix','root':'H2-D7',
         'note':'The proposed cleanup rule permits release after lease expiry without requiring confirmed remote termination. A paused worker or remote job may remain live/uncertain after local expiry. R7 requires keeping its capacity occupied until reconciliation; extending the lease does not resolve that failure.'}],
    'H1-luna':[
        {'finding':4,'category':'supported_extra_with_context','root':'precision',
         'note':'The finite-precision counterexample is verified with precision28 in additional-precision-witness.json. The dossier does not specify the actual precision or domain precision bounds; do not claim a production configuration was observed. The answer says 0.01 cents where the normalized result is EUR0.01=1 cent.'}],
    'H1-haiku':[
        {'finding':5,'category':'supported_extra_with_context','root':'precision',
         'note':'The three one-third contributions followed by -0.995 expose premature rounding before the required final half-away rounding. The post-hoc witness is checked separately; Sol/Sonnet raised precision uncertainty without this concrete witness.'},
        {'finding':8,'category':'witness_unit_slip','root':'H1-D6',
         'note':'1000 cents plus EUR50 is 6000 cents, not1050. Replacing the delta with EUR0.50 or the new balance with6000 restores the valid stale-overwrite trace; the root and proposed version guard remain correctly identified.'}],
    'H3-haiku':[
        {'finding':5,'category':'unconfirmed_finding','root':None,
         'note':'This asserts a page-cache bug assuming E2 caches individual continuation pages and that signed cursors carry positions. The dossier does not specify cache granularity or that HTTP cursors are page cursors; the worker may page internally and cache the complete export. Sonnet raised this as uncertainty. It should remain conditional, not a proven independent defect.'}]
}

def usage(record):
    u=record.get('usage_reported')
    if not isinstance(u,dict) or 'input_tokens' not in u:return None
    if record['route']['provider']=='claude':
        inp=sum(u.get(k,0) for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens'))
        cached=u.get('cache_read_input_tokens',0)
        thinking=u.get('output_tokens_details',{}).get('thinking_tokens')
    else:
        inp=u['input_tokens'];cached=u.get('cached_input_tokens',u.get('cache_read_tokens',0))
        thinking=u.get('reasoning_output_tokens',u.get('thinking_tokens'))
    out=u.get('output_tokens')
    return {'input_including_cache':inp,'cached_read_subset':cached,'output_including_thinking':out,
            'thinking_subset':thinking,'total_tokens':inp+out}

cells=[]
for key,mapping in MAPS.items():
    record=json.loads((ROOT/(key+'.json')).read_text())
    assert record['status']=='completed',key
    answer=record.get('answer')
    assert isinstance(answer,dict) and len(answer.get('findings',[]))==len(mapping),key
    case=cases[record['case']]
    assert record['prompt_sha256']==hashlib.sha256((protocol['instruction']+case['input']).encode()).hexdigest(),key
    found=set();extras=[]
    for index,item in enumerate(mapping,1):
        if isinstance(item,int) and item>0:found.add(f"{case['id']}-D{item}")
        elif isinstance(item,list):found.update(f"{case['id']}-D{n}" for n in item)
        elif isinstance(item,str):extras.append({'finding':index,'id':item})
    expected={d['id'] for d in case['oracle']}
    assert found<=expected
    cells.append({'record':key+'.json','case':case['id'],'route':record['route'],'finding_map':mapping,
                  'seeded_found':sorted(found),'seeded_expected':len(expected),'seeded_missed':sorted(expected-found),
                  'supported_extras':extras,'unconfirmed_findings':mapping.count(None),'format_valid':record['format_valid'],
                  'verdict_correct':answer.get('verdict')=='needs_changes','elapsed_seconds':record['elapsed_seconds'],
                  'usage':usage(record),'reviews':REVIEWS.get(key,[]),
                  'quota_before':record['quota_before'],'quota_after':record['quota_after']})
nonanswers=[]
pending=[]
ungraded=[]
for path in sorted(ROOT.glob('H[123]-*.json')):
    if path.stem in MAPS:continue
    r=json.loads(path.read_text())
    if r['status'] in ('prepared','running'):pending.append(path.name)
    elif r['status']!='completed' or not isinstance(r.get('answer'),dict):
        nonanswers.append({'record':path.name,'case':r['case'],'route':r['route'],'status':r['status'],
                          'elapsed_seconds':r.get('elapsed_seconds'),'usage':usage(r),
                          'quota_before':r.get('quota_before'),'quota_after':r.get('quota_after'),
                          'error_excerpt':r.get('error_excerpt'),'format_valid':r.get('format_valid',False)})
    else:ungraded.append(path.name)
summaries=[]
for route in protocol['routes']:
    group=sorted((c for c in cells if c['route']['id']==route['id']),key=lambda c:c['case'])
    if not group:continue
    failed=sorted((c for c in nonanswers if c['route']['id']==route['id']),key=lambda c:c['case'])
    observed=sorted(group+failed,key=lambda c:c['case'])
    totals={k:sum(c['usage'][k] or 0 for c in observed if c['usage'] is not None) for k in group[0]['usage']}
    summaries.append({'route':route,'cases_graded':len(group),'seeded_found':sum(len(c['seeded_found']) for c in group),
        'seeded_expected':sum(c['seeded_expected'] for c in group),'supported_extras':sum(len(c['supported_extras']) for c in group),
        'unconfirmed_findings':sum(c['unconfirmed_findings'] for c in group),
        'format_valid':sum(c['format_valid'] for c in group),'correct_verdicts':sum(c['verdict_correct'] for c in group),
        'elapsed_seconds':round(sum(c['elapsed_seconds'] for c in observed),3),'usage':totals,
        'usage_missing_calls':sum(c['usage'] is None for c in observed),'nonanswer_cases':[c['case'] for c in failed],
        'seeded_total_targets':sum(len(c['oracle']) for c in cases.values()),
        'review_caveats':sum(len(c['reviews']) for c in group),'quota_before_first':group[0]['quota_before'],
        'quota_after_last':observed[-1]['quota_after']})
result={'schema_version':1,'oracle_sha256':protocol['oracle_sha256'],
        'method':'Explicit non-blind coordinator mapping against predeclared root oracle; supported extras/correction caveats reviewed separately. No general capability ranking or unsupported exact false-positive rate.',
        'graded_target_cells':len(cells),'planned_target_cells':15,'cells':cells,'summaries':summaries,
        'nonanswers':nonanswers,'pending':pending,'ungraded':ungraded,
        'grading_scope':'Seeded recall does not prove that every explanation or fix is sound. Fix alternatives and arithmetic are explicitly reviewed; private reasoning is not inspected.'}
(ROOT/'adjudication.json').write_text(json.dumps(result,indent=2)+'\n')
for s in summaries:print(s['route']['id'],str(s['seeded_found'])+'/'+str(s['seeded_expected']),s['usage']['total_tokens'],s['elapsed_seconds'],'seconds',s['format_valid'],'valid JSON')
