"""Render complete hard-analysis evidence, including failures and unknown usage."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'adjudication.json').read_text())
protocol=json.loads((ROOT/'protocol.json').read_text())
cases=json.loads((ROOT/'cases.json').read_text())
assert not data['pending'] and not data['ungraded'], 'Wait for completion and explicit adjudication'
assert len(data['cells'])+len(data['nonanswers'])==15
order=['sonnet','sol','luna','haiku','gemini']
labels={'sonnet':'Sonnet 5.5 high','sol':'GPT-6.1 Sol high','luna':'GPT-6 Luna max','haiku':'Haiku 5.5 max','gemini':'Gemini 3.8 Flash high'}
summaries={s['route']['id']:s for s in data['summaries']}
lines=['# Three difficult analyses across five model routes','',
       '## Protocol and scope','',
       'The owner requested three additional, very complex analyses with every model from the prior ladder. Fifteen target calls use identical user input per dossier. The three dossiers cross authoritative requirements, verified protections, candidate code, lifecycle traces and superseded design memos. Each has eight predeclared independent defects; 24 frozen roots in total. Oracle SHA-256: `'+protocol['oracle_sha256']+'`. Arithmetic and modeled counterexample checks ran before model calls. Models never receive the oracle.','',
       'Sol, Sonnet and Gemini remain at high; Luna and Haiku at max. Full Claude model IDs are used with an effective-model guard. Codex-2 runs both OpenAI models; Claude Work runs both Claude models; Antigravity runs Gemini. There is one native call per account at a time, at most three accounts concurrently. Within accounts the model groups run sequentially. No fallback or automatic model retry is configured.','',
       'The common output contract is one JSON object, at most 12 independent findings and 1,800 whitespace-delimited words. The protocol has a 900-second deadline with a 30-second CLI watchdog allowance; Antigravity additionally receives native --print-timeout=900s. This is a new condition, not the previous ladder\'s 900-word/300-second setting.','',
       'This pilot is outside the formal REQ-024 corpus, frozen manifest and T19 reviewer records. One synthetic run per cell is not a statistical capability ranking. Coordinator adjudication is explicit and non-blind. Quota is coarse account telemetry, can lag or include other activity; hidden CLI contexts/tokenizers/cache accounting differ.','',
       '## Dossiers','',
       '| ID | Analysis | Frozen defects |','|---|---|---:|']
for c in cases:lines.append(f"| {c['id']} | {c['title']} | {len(c['oracle'])} |")
lines += ['', '## Coverage and execution per dossier','',
          'Each completed cell shows frozen roots found/expected and wall seconds. Supported post-hoc discoveries are separate. A failed/no-answer cell is not scored as an intellectual miss; it delivered no review within the measured attempt.','',
          '| Dossier | '+' | '.join(labels[m] for m in order)+' |','|---|'+'---|'*5]
for case in cases:
    row=[case['id']]
    for model in order:
        cell=next((c for c in data['cells'] if c['case']==case['id'] and c['route']['id']==model),None)
        if cell:
            suffix=f" +{len(cell['supported_extras'])} extra" if cell['supported_extras'] else ''
            row.append(f"{len(cell['seeded_found'])}/{cell['seeded_expected']}{suffix} · {cell['elapsed_seconds']:.1f}s")
        else:
            f=next(c for c in data['nonanswers'] if c['case']==case['id'] and c['route']['id']==model)
            row.append(f"{f['status']} · {f['elapsed_seconds']:.1f}s")
    lines.append('| '+' | '.join(row)+' |')
lines += ['', '## Measured tokens and time','',
    'Time is the sum of native call wall times, including startup/provider latency, not the total parallel experiment duration. Input includes cache creation/read. Output includes thinking; thinking is a subset, not an extra charge added to output. Missing usage is unknown, never zero. No API-dollar equivalence is inferred from subscription calls.','',
    '| Route | Graded roots | Usable JSON | Input incl. cache | Cache-read subset | Output incl. thinking | Thinking subset | Reported total | Time sum |',
    '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for m in order:
    s=summaries[m];u=s['usage'];unknown=' + unknown' if s['usage_missing_calls'] else ''
    lines.append(f"| {labels[m]} | {s['seeded_found']}/{s['seeded_expected']} graded | {s['format_valid']}/3 | {u['input_including_cache']:,}{unknown} | {u['cached_read_subset']:,} | {u['output_including_thinking']:,}{unknown} | {u['thinking_subset']:,}{unknown} | {u['total_tokens']:,}{unknown} | {s['elapsed_seconds']:.1f}s |")
lines += ['', '## What seeded recall does not show','',
    'The 24-root denominator stays frozen. Luna and Haiku also provide concrete finite-precision witnesses for H1: rounded Decimal division before aggregation can change the final cent. Luna\'s precision-28 witness and Haiku\'s three one-third contributions followed by -0.995 are verified in separate post-hoc JSONs; the latter is checked at precision28 and50. Sol and Sonnet raise the precision question as uncertainty. This additional finding is reported separately, with the unspecified actual precision/domain bounds disclosed.','',
    'Two kinds of correction weakness matter independently of root detection. Gemini H2 permits cleanup on local lease expiry without remote termination proof; a job can remain live/uncertain afterward. Its hash-only quota-evidence alternative cannot reproduce a lost cache snapshot. Sonnet H2 has a correct primary reconciliation rule, but its alternative of only coupling reservation expiry to the lease needs that same reconciliation rule retained. Explicit counterexamples are in `fix-counterexamples.json`.','',
    'Detailed review caveats (including arithmetic/unit slips) follow. They are not silently converted into false-positive root findings or hidden by the all-seeds-found score.','']
for c in data['cells']:
    for review in c['reviews']:
        lines.append(f"- `{c['record']}`, finding {review['finding']} ({review['category']}): {review['note']}")
lines += ['', '## Before/after account quota','',
    'Percentages are USED. Each model row uses the reading immediately before its first call and after its last call. Models sharing an account run serially, but delayed service accounting can cross model boundaries; zero displayed change does not mean zero cost. All observation/reset timestamps and statuses are in the per-call records.','',
    '| Route | Account | 5h used before → after | 7d used before → after | Read status |','|---|---|---:|---:|---|']
def pct(row,name):return row.get('windows',{}).get(name,{}).get('used_percent','unknown')
for m in order:
    s=summaries[m];b=s['quota_before_first'];a=s['quota_after_last']
    lines.append(f"| {labels[m]} | {s['route']['profile']} | {pct(b,'five_hour')} → {pct(a,'five_hour')}% | {pct(b,'seven_day')} → {pct(a,'seven_day')}% | {b.get('status')} / {a.get('status')} |")
if (ROOT/'quota-final.json').exists():
    lines += ['', 'Final delayed account snapshot:','']
    for q in json.loads((ROOT/'quota-final.json').read_text()):
        lines.append(f"- {q['profile']}: 5h {pct(q,'five_hour')}%, 7d {pct(q,'seven_day')}% used; status={q['status']}.")
lines += ['', '## Completion evidence and limits','',
    '`cases.json` contains the frozen dossiers/oracle. `protocol.json` pins instructions, routes, output ceilings, deadlines and executable hashes. `oracle-checks.json` records the pre-call deterministic checks. Per-cell JSON retains final response, numeric usage, prompt hash, requested/effective model evidence and quota; private thinking text/raw CLI streams are not persisted by this harness.','',
    '`adjudication.json`/`grade.py` expose every manual finding-to-root mapping, supported extra and correction caveat. `execution-summary.json` retains native lane completion/failure. `validation.json` records actual closing checks. Claude response metadata confirms effective model IDs; other providers retain explicit requested IDs without separately retained effective-ID confirmation in this collector.','']
for f in data['nonanswers']:
    lines.append(f"- `{f['record']}`: {f['status']}; elapsed {f['elapsed_seconds']}s; usage {'not reported' if f['usage'] is None else 'partially/fully reported as retained'}. A failed attempt is not a passing analysis.")
lines += ['', 'No Pictures/product implementation, Scheduler dispatch, approval, frozen plan, formal benchmark manifest or reviewer pair changed. P-109 remains owner-selected. This experiment measures the requested route configurations, not every possible effort level of each model.','']
(ROOT/'REPORT.md').write_text('\n'.join(lines))
print(ROOT/'REPORT.md')
