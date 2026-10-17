"""Render the measured native Planner pilot; no inferred universal winner."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
metrics=json.loads((ROOT/'metrics.json').read_text());grades=json.loads((ROOT/'adjudication.json').read_text());protocol=json.loads((ROOT/'protocol.json').read_text())
labels={'opus':'Opus 5.5 high','sol':'GPT-6.1 Sol high','astra':'GPT-6 Astra high'}
by_route={s['route']['id']:s for s in metrics['summaries']};quality={s['route']['id']:s for s in grades['summaries']}
lines=['# Native Planner comparison: Opus, Sol and Astra','',
'## Scope and controls','',
'Nine owner-authorized fresh planning calls use three pinned code snapshots/specifications, a hash-identical improved Planner role plus four private skills/references/schema, high requested effort, maximum 8 tasks, and the same two-artifact output contract. CP1: API pagination/external consumer; CP2: SQLite→PostgreSQL migration; CP3: existing analysis in CLI/web. Inputs reuse candidate C2/C3/C4 assets outside the formal matched-arm REQ-024 experiment; no formal manifest, call cap, reviewer score or product source changed.', '',
'Claude Work runs Opus with safe/restricted mode, Read/Grep/Glob only, plan permission mode, no session persistence. Codex-2 runs Sol/Astra with ignored user config/rules, read-only sandbox, disabled web and instructed read-only file inspection. Two account lanes run concurrently, one call per account; Sol/Astra order alternates by case. Tool affordances/native hidden instructions differ, so this measures operational model+native-runtime configurations, not isolated intrinsic intelligence. Exact internal reasoning budgets and Codex effective model/service tier are not independently attested.', '',
'The host validates first responses using a frozen standalone bt_planner package, then performs semantic judgement with route labels removed case by case. Coordinator had seen some route-labeled deterministic diagnostics; style and timing can reveal identity. This is partial blinding, not independent external judging. Existing candidate oracles are draft behavior checklists; actual source/SPEC override their path hints (notably CP3 already has CLI report routing). Full/partial/missing statuses require substantive plan evidence, not just covers labels.', '',
'No automatic repair turns were allowed. This is first-draft reliability, not end-to-end performance after the normal validator/repair loop. Plans were not approved/frozen or executed; checks are structural, not passing product test suites.', '',
'## Aggregate results','',
'| Route | Behavioral checklist full / partial / missing | Schema valid | Publishable first draft | Correct output blocks | Total tokens | Output incl. thinking | Native time sum | Read tool calls | Base API-equivalent USD* |',
'|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for ident in labels:
 m=by_route[ident];q=quality[ident];u=m['usage'];cost=u['illustrative_standard_api_usd'];cost='unknown' if cost is None else f'${cost:.3f}'
 lines.append(f"| {labels[ident]} | {q['full']} / {q['partial']} / {q['missing']} (13) | {q['schema_valid']}/3 | {q['publishable_first_response']}/3 | {q['valid_output_blocks']}/3 | {u['total_tokens']:,} | {u['output_including_thinking']:,} | {m['elapsed_seconds']:.3f}s | {m['tool_calls']} | {cost} |")
lines+=['', '*Illustrative baseline Standard API equivalent computed from recorded uncached/cache-read/cache-write-TTL/output classes and researched rates, not a subscription invoice. Aggregate usage does not reveal every per-request long-context/speed/tool modifier; none is fabricated. Codex credit billing has different cache-write rules. Actual account telemetry is reported separately.', '',
'Total input includes repeated/cache input across tool turns; output already includes thinking. Never add thinking twice. Time is the sum of native call wall times, not total parallel experiment elapsed time. Tokenizers, tool batching, hidden context and cache differ. Schema validity, substantive coverage and operational readiness are distinct.', '',
'## Per-case outcomes','', '| Case | Route | Checklist full / partial / missing | Validate / check / report exit | Tokens | Native seconds |','|---|---|---:|---|---:|---:|']
for c in sorted(grades['cells'],key=lambda c:(c['case'],list(labels).index(c['route']['id']))):
 exits='/'.join(str(c['checks'].get(a,{}).get('exit_code')) for a in ('validate','check','report'))
 lines.append(f"| {c['case']} | [{labels[c['route']['id']]}](outputs/{Path(c['record']).stem}/PLAN.md) | {c['full']} / {c['partial']} / {c['missing']} | {exits} | {c['usage']['total_tokens']:,} | {c['elapsed_seconds']:.3f} |")
lines+=['','## Structural failures and warnings','']
for c in sorted(grades['cells'],key=lambda c:(c['case'],c['route']['id'])):
 result=c['checks'].get('check',{}).get('result',{});errors=result.get('errors',[]);warnings=result.get('warnings',[])
 lines.append(f"- **{c['case']} / {labels[c['route']['id']]}:** {len(errors)} error(s), {len(warnings)} warning(s). "+(' '.join(errors) if errors else 'No publishability errors.'))
lines+=['', 'Warnings include verification-purpose/acceptance mismatches requiring M6 manual review; a publishable structure alone does not mean automatic execution acceptance. The legacy collector field format_valid checks a review JSON shape and is unused here; block_contract_valid is the Planner capture metric. Full diagnostics are in deterministic-checks.json.', '', '## Semantic judgements and counterexamples','']
for c in sorted(grades['cells'],key=lambda c:(c['case'],c['route']['id'])):
 lines.append(f"### {c['case']} — {labels[c['route']['id']]}\n")
 for item in c['oracle_items']:lines.append(f"- **{item['id']} {item['status']}:** {item['evidence']}")
 for note in c['notes']:lines.append(f"- Note: {note}")
 lines.append('')
lines+=['## Input/cache/output breakdown','', '| Route | Input incl. cache | Cache-read subset | Cache-write subset | Output incl. thinking | Thinking subset |','|---|---:|---:|---:|---:|---:|']
for ident in labels:
 u=by_route[ident]['usage'];lines.append(f"| {labels[ident]} | {u['input_including_cache']:,} | {u['cache_read_subset']:,} | {u['cache_write_subset']:,} | {u['output_including_thinking']:,} | {u['thinking_subset']:,} |")
lines+=['','## Quota observations','', 'Percentages are USED. First-before failures remain unknown; no nearby/cached value is relabeled as a baseline. Codex-2 serves both models serially, and subscription readings are rounded/lagged, so even per-cell deltas cannot establish an exact stable per-model quota price.', '', '| Account | First-before status | 5h used before → delayed after | Weekly used before → delayed after | Final status |','|---|---|---:|---:|---|']
records=[json.loads(p.read_text()) for p in sorted(ROOT.glob('CP[123]-*.json')) if '-files-' not in p.name]
final=json.loads((ROOT/'quota-final.json').read_text()) if (ROOT/'quota-final.json').exists() else []
def pct(q,window):
 v=q.get('windows',{}).get(window,{}).get('used_percent');return 'unknown' if v is None else f'{v:g}%'
for profile in ('codex-2','claude-work'):
 group=sorted([r for r in records if r['route']['profile']==profile],key=lambda r:r['started_at']);before=group[0]['quota_before'];after=next((x for x in final if x['profile']==profile),{})
 lines.append(f"| {profile} | {before.get('status')} | {pct(before,'five_hour')} → {pct(after,'five_hour')} | {pct(before,'seven_day')} → {pct(after,'seven_day')} | {after.get('status','not read')} |")
lines+=['', 'Observed within-cell deltas (percentage points, rounded and lagged):']
for row in metrics.get('observed_quota_deltas',[]):
    five=row['five_hour'];week=row['seven_day']
    lines.append(f"- {labels[row['route']]}: 5h known sum {five['known_observed_change_points']:g}pp ({five['unknown_cells']} unknown cells); weekly known sum {week['known_observed_change_points']:g}pp ({week['unknown_cells']} unknown cells).")
lines+=['', 'For Codex-2, all six readings have matching reset windows: Sol cells sum +11pp/2pp (5h/weekly), Astra +43pp/7pp. These add to the observed account change, but are not an exact stable model price. Claude has one unknown first-before reading; its last immediate 5h reading was15%, delayed17%, so the extra delayed2pp is not assigned to a particular call.']
issues=[{'cell':r['case']+'-'+r['route']['id'],'side':side,'status':r.get(side,{}).get('status')} for r in records for side in ('quota_before','quota_after') if r.get(side,{}).get('status')!='ok']
lines+=['',f'Non-ok quota reads: `{json.dumps(issues)}`.', '', '## Evidence and limitations','',
'PLAN.md fixes scope/controls. cases.json pins source archive/spec/oracle bytes; source-hashes.json pins the shared bundle. protocol.json pins the task/runner/base collector. runtime-versions.json records CLI versions; validator-hashes.json pins the host validator. Each native record retains the final answer, tool names/read arguments, numeric usage and quota. Per-cell files-before manifests and workspace_changes document net source integrity; these are before/after checks, not proof against transient reverted edits or unseen out-of-scope reads. No raw private thinking text or full raw streams are retained.', '',
'Outputs are preserved under outputs/<case>-<route>/PLAN.md and PLAN.json. blind-plans.json, blind-judgements.json and blind-key.json expose the route-hidden judgement/unblinding trail. Metrics and structural diagnostics remain separate from semantic judgements. The scratch workspace is retained outside the repository and can be reconstructed from pinned archives.', '',
'Three heterogeneous cases and one response per cell do not estimate general failure probability, guarantee production readiness or measure quality after feedback/repair. This pilot does not resolve formal T17 account/isolation gates or select a production Planner. No change to the D-063 reviewer policy, no product implementation, no Scheduler dispatch, no provider fallback or additional review-model calls occurred.']
rendered='\n'.join(lines)+'\n'
if (ROOT/'INTERPRETATION.md').exists():rendered=rendered.replace('## Scope and controls',(ROOT/'INTERPRETATION.md').read_text()+'\n## Scope and controls',1)
(ROOT/'REPORT.md').write_text(rendered);print(ROOT/'REPORT.md')
