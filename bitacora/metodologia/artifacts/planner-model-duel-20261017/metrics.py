"""Numeric native usage and illustrative Standard API equivalents, not invoices."""
from decimal import Decimal
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rates={'opus':{'input':4,'cache':0.2,'write5m':5,'write1h':8,'output':20},'sol':{'input':2,'cache':0.1,'write':2.5,'output':10},'astra':{'input':10,'cache':1,'write':12.5,'output':50}}
def usage(r):
 u=r.get('usage_reported')
 if not isinstance(u,dict) or 'input_tokens' not in u:return None
 route=r['route']['id'];p=rates[route];known=True
 if r['route']['provider']=='claude':
  uncached=u['input_tokens'];cached=u.get('cache_read_input_tokens',0);created=u.get('cache_creation_input_tokens',0);inp=uncached+cached+created
  split=u.get('cache_creation',{});one=split.get('ephemeral_1h_input_tokens');five=split.get('ephemeral_5m_input_tokens');thinking=u.get('output_tokens_details',{}).get('thinking_tokens')
  if created and (one is None or five is None or one+five!=created):cost=None;known=False
  else:cost=(uncached*p['input']+cached*p['cache']+(one or 0)*p['write1h']+(five or 0)*p['write5m'])/1e6
 else:
  inp=u['input_tokens'];cached=u.get('cached_input_tokens',0);created=u.get('cache_write_input_tokens');uncached=inp-cached-(created or 0);thinking=u.get('reasoning_output_tokens')
  known=created is not None
  cost=(uncached*p['input']+cached*p['cache']+(created or 0)*p['write'])/1e6 if known else None
 out=u.get('output_tokens')
 if cost is not None and out is not None:cost+=out*p['output']/1e6
 return {'input_including_cache':inp,'cache_read_subset':cached,'cache_write_subset':created,'uncached_input':uncached,'output_including_thinking':out,'thinking_subset':thinking,'total_tokens':inp+out if out is not None else None,'illustrative_standard_api_usd':round(cost,6) if cost is not None else None,'api_equivalent_known':known,'api_rate_source':'planner-model-research-20261017.md; rates checked 2026-10-17; no tool/long-context/speed surcharge inferred'}
records=[]
for path in sorted(ROOT.glob('CP[123]-*.json')):
 if '-files-' in path.name:continue
 r=json.loads(path.read_text());records.append({'record':path.name,'case':r['case'],'route':r['route'],'status':r['status'],'elapsed_seconds':r.get('elapsed_seconds'),'block_contract_valid':r.get('block_contract_valid'), 'tool_calls':len(r.get('tool_audit',[])),'usage':usage(r),'quota_before':r.get('quota_before'),'quota_after':r.get('quota_after'),'workspace_changes':r.get('workspace_changes')})
summaries=[]
for route in ('opus','sol','astra'):
 group=[r for r in records if r['route']['id']==route and r['status'] not in ('running','prepared')];observed=[r for r in group if r['usage'] is not None]
 if not observed:continue
 keys=['input_including_cache','cache_read_subset','cache_write_subset','uncached_input','output_including_thinking','thinking_subset','total_tokens','illustrative_standard_api_usd']
 totals={k:sum(r['usage'][k] for r in observed) if all(r['usage'][k] is not None for r in observed) else None for k in keys}
 if totals['illustrative_standard_api_usd'] is not None:totals['illustrative_standard_api_usd']=round(totals['illustrative_standard_api_usd'],6)
 summaries.append({'route':group[0]['route'],'calls_finished':len(group),'usage_missing_calls':len(group)-len(observed),'elapsed_seconds':round(sum(r['elapsed_seconds'] or 0 for r in group),3),'tool_calls':sum(r['tool_calls'] for r in group),'valid_output_blocks':sum(bool(r['block_contract_valid']) for r in group),'usage':totals})
quota_deltas=[]
for route in ('opus','sol','astra'):
    group=[r for r in records if r['route']['id']==route and r['status'] not in ('running','prepared')]
    item={'route':route,'scope':'Sum of observed within-cell percentage-point changes, not exact causal subscription cost. Excludes later unassigned lag changes.'}
    for window in ('five_hour','seven_day'):
        values=[];unknown=0
        for r in group:
            before=r.get('quota_before') or {};after=r.get('quota_after') or {}
            b=before.get('windows',{}).get(window,{});a=after.get('windows',{}).get(window,{})
            if before.get('status')!='ok' or after.get('status')!='ok' or b.get('used_percent') is None or a.get('used_percent') is None or b.get('resets_at')!=a.get('resets_at'):
                unknown+=1
            else:values.append(a['used_percent']-b['used_percent'])
        item[window]={'known_observed_change_points':sum(values),'unknown_cells':unknown,'complete_observed_sum_points':sum(values) if not unknown else None}
    quota_deltas.append(item)
result={'schema_version':1,'rates':rates,'records':records,'summaries':summaries,'observed_quota_deltas':quota_deltas,'limits':'Raw totals include repeated/cache inputs and output thinking. API equivalents are hypothetical based on recorded classes at Standard rates, not billed subscription dollars; service tier not independently attested. No exact per-task quota cost is inferred.'}
(ROOT/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
for s in summaries:print(s['route']['id'],s['calls_finished'],'finished',s['usage']['total_tokens'],'tokens',s['elapsed_seconds'],'s','API-equivalent',s['usage']['illustrative_standard_api_usd'])
