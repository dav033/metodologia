"""Render measured effort comparisons without equating tokens and subscription cost."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
pr=json.loads((ROOT/'protocol.json').read_text());a=json.loads((ROOT/'adjudication.json').read_text());cases=json.loads((ROOT/'cases.json').read_text());s={x['route']['id']:x for x in a['summaries']}
labels={'sol-medium':'Sol 6.1 medium','sol-high':'Sol 6.1 high','sonnet-medium':'Sonnet 5.5 medium','sonnet-high':'Sonnet 5.5 high'}
lines=['# Sol / Sonnet medium versus high: three difficult cases','',
       '## Scope and method','',
       'The owner authorized 12 native calls: identical input per case to each model/effort route. Cases contain 31 frozen expected roots (11/10/10). Each response has the same one-JSON/12-findings/1,800-word ceiling and 900s deadline plus 30s watchdog allowance. Codex-2 and Claude Work run one call at a time each, in parallel account lanes; effort order alternates per case and between lanes. Every cell uses a fresh ephemeral session with tools disabled/requested unused. Full Claude IDs are checked; requested effort is captured in flags, not independently attested by response metadata. Codex effective identity is not separately retained by this collector.',
       '',f"Oracle SHA-256: `{pr['oracle_sha256']}`. Thirty-one deterministic arithmetic/modeled-trace checks ran before provider calls. These are synthetic dossier witnesses, not product integration tests. `PLAN.md` fixes adjudication criteria. Answers were shuffled and stripped of route/effort before coordinator adjudication; the saved blind judgements preceded unblinding. Writing style may reveal identity. This is not independent external judging, a statistically powered benchmark, or the formal REQ-024 corpus.",
       '', '## Dossiers','', '| Case | Scenario | Frozen roots |','|---|---|---:|']
for c in cases:lines.append(f"| {c['id']} | {c['title']} | {len(c['oracle'])} |")
lines+=['','## Results','', '| Route | Roots found | Valid JSON | Total tokens | Input incl. cache | Cache-read subset | Output incl. thinking | Thinking subset | Wall sum |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for ident in labels:
 x=s[ident];u=x['usage'];lines.append(f"| {labels[ident]} | {x['seeded_found']}/31 | {x['valid_json']}/3 | {u['total_tokens']:,} | {u['input_including_cache']:,} | {u['cached_read_subset']:,} | {u['output_including_thinking']:,} | {u['thinking_subset']:,} | {x['elapsed_seconds']:.3f}s |")
lines+=['','Input includes cache creation/read where applicable. Thinking is already included in output and is never added twice. Wall sums include native startup/provider latency; they are not the parallel experiment duration. Tokenizers, hidden CLI context and cache differ; raw totals are not equal monetary or subscription cost.', '', '## Matched effort differences','', '| Model | High minus medium roots | High vs medium total tokens | High vs medium output | High vs medium time |','|---|---:|---:|---:|---:|']
for model in ('sol','sonnet'):
 m=s[model+'-medium'];h=s[model+'-high'];pct=lambda key:100*(h['usage'][key]/m['usage'][key]-1)
 lines.append(f"| {model} | {h['seeded_found']-m['seeded_found']:+d} | {pct('total_tokens'):+.1f}% | {pct('output_including_thinking'):+.1f}% | {100*(h['elapsed_seconds']/m['elapsed_seconds']-1):+.1f}% |")
lines+=['','## Per-case results','', '| Case | Route | Roots | Total tokens | Output | Time |','|---|---|---:|---:|---:|---:|']
for c in sorted(a['cells'],key=lambda x:(x['case'],list(labels).index(x['route']['id']))):
 lines.append(f"| {c['case']} | {labels[c['route']['id']]} | {len(c['seeded_found'])}/{c['seeded_expected']} | {c['usage']['total_tokens']:,} | {c['usage']['output_including_thinking']:,} | {c['elapsed_seconds']:.3f}s |")
lines+=['','## Correction quality, additional findings and uncertainty','', 'Seeded detection and correction soundness are separate. The following notes preserve the route-hidden judgements; supported extras do not enlarge the denominator. Absence of a note means no concrete additional error was established in this review, not a proof of universally correct repairs.']
for c in sorted(a['cells'],key=lambda x:(x['case'],x['route']['id'])):
 for n in c['notes']:lines.append(f"\n- **{c['case']} / {labels[c['route']['id']]}**: {n}")
 for e in c['extras']:lines.append(f"\n- **{c['case']} / {labels[c['route']['id']]}**, finding {e['finding']}: extra `{e['extra']}`; see judgement notes.")
 if c['seeded_missed']:lines.append(f"\n- **{c['case']} / {labels[c['route']['id']]}** missed: {', '.join(c['seeded_missed'])}.")
lines+=['','## Account quota before and after','', 'Percentages are USED. Efforts interleave on the same account; first/last route boundary readings overlap other effort calls and cannot identify effort-specific consumption. Rounded service telemetry can lag and include unrelated activity. Missing or HTTP429 readings remain unknown; unchanged displayed values do not mean zero cost. Every before/after/reset/status sample is preserved in its cell.', '', '| Account | 5h before → delayed after | Weekly before → delayed after | Status |','|---|---:|---:|---|']
final=json.loads((ROOT/'quota-final.json').read_text()) if (ROOT/'quota-final.json').exists() else []
records=[json.loads(p.read_text()) for p in ROOT.glob('E*-*.json')]
def value(q,window):
 v=q.get('windows',{}).get(window,{}).get('used_percent');return 'unknown' if v is None else f'{v:g}%'
for profile in ('codex-2','claude-work'):
 group=sorted([r for r in records if r['route']['profile']==profile],key=lambda r:r['started_at']);before=group[0]['quota_before'];after=next((q for q in final if q['profile']==profile),{})
 lines.append(f"| {profile} | {value(before,'five_hour')} → {value(after,'five_hour')} | {value(before,'seven_day')} → {value(after,'seven_day')} | {before.get('status')} / {after.get('status','not read')} |")
errors=[(r['case'],r['route']['id'],side,r[side]['status']) for r in records for side in ('quota_before','quota_after') if r[side]['status']!='ok']
lines+=['',f'Non-ok per-call quota reads: `{json.dumps(errors)}`.', '', '## Evidence and limits','',
       '`cases.json` contains the frozen input/oracle; `oracle-checks.json` the pre-call witness checks; `protocol.json` the routes, order, limits and executable hashes; `runtime-versions.json` the native versions; 12 cell records contain final answers, usage and metadata. Raw/private thinking text is not saved. `blind-answers.json`, `blind-judgements.json` and `blind-key.json` expose the grading/unblinding trail; `adjudication.json` records exact root mappings, extras and metrics. `validation.json` retains actual closeout checks.', '',
       'One run per route/case cannot estimate failure probability or prove general effort superiority. Cases are dense with explicit snippet/contract references; this helps isolate review reasoning but does not measure repository exploration, coding, long-session execution or undisclosed production complexity. Fixes are judged against the supplied contracts, not implemented in product code. Cache/order and runtime overhead remain confounders. No reviewer selection, formal benchmark freeze, Scheduler dispatch, source implementation or routing-policy change occurred.']
rendered='\n'.join(lines)+'\n'
rendered=rendered.replace('## Scope and method','## Interpretation\n\nWithin these three cases, high did not increase seeded detection or verified extra findings for either model. Sol medium and high both found the additional remote-worker epoch-fencing defect and proposed a suitable guard. Both Sonnet efforts treated that risk as uncertainty and their convergence/key suggestions do not prevent the demonstrated stale-command regression. Sonnet high improved some E1 detail but added an unsupported E2 cardinality aside; there is no consistent measured quality gain from high here.\n\nSonnet medium used the fewest raw total tokens (41,002); Sol medium produced the fewest output/thinking tokens (7,000) and had the strongest grounded correction record in these particular answers, with nearly equal time to Sonnet medium. High raised Sol total tokens/output/time by 4.5%/44.6%/55.1%, and Sonnet by 11.0%/26.8%/29.2%. This supports starting these review workloads at medium and escalating on a demonstrated unresolved issue, while leaving general production effort policy undecided.\n\n'+'## Scope and method',1)
(ROOT/'REPORT.md').write_text(rendered)
print(ROOT/'REPORT.md')
