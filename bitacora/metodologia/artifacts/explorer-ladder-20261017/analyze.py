"""Read native records, preserve unknown measurements, check cited files/lines."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORK=Path(json.loads((ROOT/'workspace.json').read_text())['root'])
SOURCE=WORK/'source'/'repo'

def usage(record):
    u=record.get('usage_reported')
    if not isinstance(u,dict) or not u:return None
    p=record['route']['provider']
    if p=='claude':
        uncached=u.get('input_tokens');cache=u.get('cache_read_input_tokens');write=u.get('cache_creation_input_tokens')
        inp=uncached+cache+write if all(type(v) is int for v in (uncached,cache,write)) else None
        out=u.get('output_tokens');thinking=u.get('output_tokens_details',{}).get('thinking_tokens')
    elif p=='codex':
        inp=u.get('input_tokens');cache=u.get('cached_input_tokens');write=u.get('cache_write_input_tokens');out=u.get('output_tokens')
        uncached=inp-cache-write if all(type(v) is int for v in (inp,cache,write)) else None
        thinking=u.get('reasoning_output_tokens')
    else:
        inp=u.get('input_tokens');cache=u.get('cache_read_tokens');write=None;out=u.get('output_tokens');thinking=u.get('thinking_tokens')
        uncached=inp-cache if all(type(v) is int for v in (inp,cache)) else None
    total=inp+out if type(inp) is int and type(out) is int else None
    return {'input_including_cache':inp,'uncached_input':uncached,'cache_read_subset':cache,'cache_write_subset':write,
            'output_including_thinking':out,'thinking_subset':thinking,'total_tokens':total,
            'reported_total_tokens':u.get('total_tokens')}

def delta(record):
    result={}
    b=record.get('quota_before') or {};a=record.get('quota_after') or {}
    for window in ('five_hour','seven_day'):
        bw=b.get('windows',{}).get(window,{});aw=a.get('windows',{}).get(window,{})
        known=b.get('status')=='ok' and a.get('status')=='ok' and all(type(v) in (int,float) for v in (bw.get('used_percent'),aw.get('used_percent'))) and bw.get('resets_at')==aw.get('resets_at')
        result[window]={'observed_change_points':round(aw['used_percent']-bw['used_percent'],4) if known else None,
                        'same_reset':bw.get('resets_at')==aw.get('resets_at') if bw and aw else None}
    return result

def citations(answer):
    found=[]
    if not isinstance(answer,dict):return found
    for a in answer.get('answers',[]):
        if not isinstance(a,dict):continue
        for ref in a.get('evidence',[]):
            if not isinstance(ref,dict):continue
            path=ref.get('path','');target=(SOURCE/path).resolve()
            inside=target.is_relative_to(SOURCE.resolve())
            exists=inside and target.is_file()
            lines=target.read_text().splitlines() if exists else []
            start=ref.get('start_line');end=ref.get('end_line')
            valid=exists and type(start) is int and type(end) is int and 1<=start<=end<=len(lines)
            found.append({'question':a.get('id'),'reference':ref,'path_exists':exists,'range_valid':valid,
                          'span_lines':end-start+1 if valid else None})
    return found

def main():
    records=[]
    for p in sorted([*ROOT.glob('E[1-6]-*.json'),*(ROOT/'gemini-recovery').glob('E[1-6]-*.json')]):
        r=json.loads(p.read_text())
        if not isinstance(r,dict) or 'route' not in r:continue
        if r.get('included_in_comparison') is False:continue
        semantic=r.get('answer')
        recovered=False
        if p.name=='E3-haiku.json' and (ROOT/'semantic-recovery.json').exists():
            semantic=json.loads((ROOT/'semantic-recovery.json').read_text())['answer'];recovered=True
        try:raw_json=json.loads(r.get('response_text',''));json_valid=isinstance(raw_json,dict)
        except (ValueError,TypeError):json_valid=False
        records.append({'record':str(p.relative_to(ROOT)),'case':r['case'],'route':r['route'],'status':r['status'],
                        'elapsed_seconds':r.get('elapsed_seconds'),'format_valid':r.get('format_valid'),
                        'raw_json_valid':json_valid,'semantic_only_recovery':recovered,
                        'response_words':r.get('response_words'),'observed_models':r.get('observed_models'),
                        'tool_calls_observed':None if r['route']['provider']=='antigravity' else len(r.get('tool_audit',[])),'usage':usage(r),
                        'quota_before':r.get('quota_before'),'quota_after':r.get('quota_after'),'quota_delta':delta(r),
                        'workspace_changes':r.get('workspace_changes'),'citations':citations(semantic)})
    groups=[]
    for scope,ids in [('all-six',{'E1','E2','E3','E4','E5','E6'}),('hard-matched',{'E4','E5','E6'})]:
        for rid in ('luna','haiku','gemini','sol','sonnet'):
            cells=[r for r in records if r['route']['id']==rid and r['case'] in ids]
            finished=[r for r in cells if r['status'] not in ('running','prepared')]
            measured=[r for r in finished if r['usage'] is not None]
            numeric={}
            for k in ('input_including_cache','uncached_input','cache_read_subset','cache_write_subset','output_including_thinking','thinking_subset','total_tokens'):
                numeric[k]=sum(r['usage'][k] for r in measured) if measured and all(r['usage'][k] is not None for r in measured) else None
            groups.append({'scope':scope,'route':rid,'cells_finished':len(finished),'completed':sum(r['status']=='completed' for r in finished),
                           'format_valid':sum(bool(r['format_valid']) for r in finished),'usage_missing':len(finished)-len(measured),
                           'wall_seconds_sum':round(sum(r['elapsed_seconds'] or 0 for r in finished),3),
                           'tool_calls_observed':sum(r['tool_calls_observed'] for r in finished) if all(r['tool_calls_observed'] is not None for r in finished) else None,
                           'usage_observed':numeric,'quota_observed_change_sum':{w:sum(v) if len(v:=[r['quota_delta'][w]['observed_change_points'] for r in finished if r['quota_delta'][w]['observed_change_points'] is not None])==len(finished) and v else None for w in ('five_hour','seven_day')}})
    (ROOT/'metrics.json').write_text(json.dumps({'schema_version':1,'records':records,'groups':groups,
        'limits':'Raw tokens include repeated/cache input; thinking is an output subset, never add twice. Observed rounded quota deltas are not exact causal prices. Missing usage or reset changes remain unknown. Partial usage sums are lower bounds.'},indent=2)+'\n')
    for g in groups:
        if g['cells_finished']:print(g['scope'],g['route'],g['cells_finished'],'finished',g['usage_observed']['total_tokens'],'observed tokens',g['wall_seconds_sum'],'s')

if __name__=='__main__':main()
