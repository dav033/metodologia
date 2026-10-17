"""Render the measured cells and explicit adjudication without inventing data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "adjudication.json").read_text())
cases = json.loads((ROOT / "cases.json").read_text())
assert len(data["cells"]) == 25, "Finish/adjudicate all requested cells before producing final report"
order = ["gpt-6.1-sol", "sonnet", "gemini-3.8-flash-high", "gpt-6-luna", "claude-haiku-5-5"]
labels = {"gpt-6.1-sol": "GPT-6.1 Sol high", "sonnet": "Claude Sonnet 5.5 high",
          "gemini-3.8-flash-high": "Gemini 3.8 Flash high", "gpt-6-luna": "GPT-6 Luna max",
          "claude-haiku-5-5": "Claude Haiku 5.5 max"}
summaries = {s["model"]: s for s in data["summaries"]}
lines = ["# Five-model synthetic plan-review ladder", "", "## Protocol", "",
    "The owner authorized five additional reviews of increasing complexity, first with three models and then with Haiku and Luna added at max effort. Each case has identical user input across models, a predeclared hidden defect oracle, correct baseline guarantees as decoys, at most eight findings and 900 visible words. Five cases contain 20 independent planted defects. The oracle was frozen before provider calls; its SHA-256 is `" + data["oracle_sha256"] + "`.", "",
    "This is a self-contained synthetic reviewer pilot outside REQ-024's formal corpus, manifest and 66 T19 review records. Its C1–C5 labels are local to this pilot. No repository exploration or implementation was requested. One run per cell cannot establish general model superiority. Adjudication is an explicit, non-blind coordinator mapping; complete final responses and mappings are provided for audit.", "",
    "Original routes use high effort; the two additional routes use max as requested. CLI versions: Codex 0.163.0, Claude Code 2.1.301, Antigravity 1.4.0. Codex runs on Codex-2; both Claude models on Claude Work; Gemini on the single Antigravity account. Calls on the same account do not overlap within this experiment. No fallback model was configured.", "",
    "## Increasing complexity", "", "| Case | Level | Topic | Predeclared defects |", "|---|---:|---|---:|"]
for c in cases:
    lines.append(f"| {c['id']} | {c['level']} | {c['title']} | {len(c['oracle'])} |")
lines += ["", "## Defect coverage and time per case", "", "Each cell shows unique planted defects found / expected, then CLI wall seconds. Asterisk means manual recovery was required and the machine output contract failed.", "",
          "| Case | " + " | ".join(labels[m] for m in order) + " |",
          "|---|" + "---|" * len(order)]
for c in cases:
    row = [c["id"]]
    for m in order:
        cell = next(x for x in data["cells"] if x["case"] == c["id"] and x["requested_model"] == m)
        star = "*" if not cell["automatically_usable"] else ""
        row.append(f"{len(cell['detected'])}/{cell['expected']} · {cell['elapsed_seconds']:.1f}s{star}")
    lines.append("| " + " | ".join(row) + " |")
lines += ["", "## Aggregate measured usage", "", "Time is the sum of five independent CLI calls, including startup/provider latency; it is not the elapsed duration of the whole parallel experiment. Input includes cache reads/creation. Output includes thinking, so thinking is a subset and must not be added again. Provider tokenizers and hidden system contexts differ; these are measurements of the local model/CLI/account routes.", "",
    "| Model | Defects | Usable JSON | Input | Cache-read subset | Output | Thinking subset | Total | Seconds |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for m in order:
    s=summaries[m];u=s["tokens"]
    lines.append(f"| {labels[m]} | {s['detected']}/{s['expected']} | {s['automatically_usable_cases']}/5 | {u['input_including_cache']:,} | {u['cached_read_input']:,} | {u['output_including_thinking']:,} | {u['thinking_subset']:,} | {u['total_tokens']:,} | {s['elapsed_seconds_sum']:.1f} |")
lines += ["", "## Focus and efficiency", "", "Duplicate test-coverage restatements count once with the underlying defect. Additional concerns without enough evidence are tracked as unconfirmed, not automatically declared false positives. Precision/F1 bounds are conservative/optimistic adjudication bounds, not statistical confidence intervals.", "",
    "| Model | Duplicate findings | Unconfirmed concerns | Precision bounds | F1 bounds | Tokens / planted defect | Seconds / planted defect |",
    "|---|---:|---:|---:|---:|---:|---:|"]
for m in order:
    s=summaries[m]
    lines.append(f"| {labels[m]} | {s['duplicates']} | {s['unconfirmed_concerns']} | {100*s['precision_bounds'][0]:.1f}–100% | {100*s['f1_bounds'][0]:.1f}–{100*s['f1_bounds'][1]:.1f}% | {s['tokens_per_detected_defect']:,.1f} | {s['seconds_per_detected_defect']:.2f} |")
lines += ["", "## Interpretation", "",
    "All five routes found all 20 planted roots. Sol high was the most focused: no separate duplicate/unconfirmed findings, the fewest output tokens, and five usable outputs. Luna max was 7.8% faster in summed time, with 2.46x Sol's output tokens. Sonnet had the smallest reported total including cache, but its C5 response broke both JSON-only and 900-word requirements. Gemini took 2.14x Sol's time. Haiku max took 8.1x Sol's time and generated 49.08x its output tokens, with no additional planted-root coverage; 215,254 of its 224,598 output tokens were thinking. This does not establish general capability rankings or dollar/subscription cost equivalence.", "",
    "## Per-model account quota observations", "", "Percentages are USED, not remaining. Each row uses the reading just before the first model call and immediately after its last call. Readings are coarse, can lag, and may include other account activity. The two excluded alias calls occurred between the Sonnet and Haiku batches; their delayed reporting may affect Claude account deltas even though their tokens/time are excluded from the model table. Reset changes must be inspected before attributing a delta.", "",
    "| Model | Account | 5h used before → after | 7d used before → after | Read status |",
    "|---|---|---:|---:|---|"]
def windows(row,name):
    return row.get("windows",{}).get(name,{}).get("used_percent","unknown")
for m in order:
    s=summaries[m];b=s["quota_before_first"];a=s["quota_after_last"]
    lines.append(f"| {labels[m]} | {b['profile']} | {windows(b,'five_hour')} → {windows(a,'five_hour')}% | {windows(b,'seven_day')} → {windows(a,'seven_day')}% | {b['status']} / {a['status']} |")
lines += ["", "Every per-call before/after sample, observation time and reset time is retained in its result JSON. The final delayed account snapshot (more than two minutes after the last call) reports Codex-2 at 2%/0%, Claude Work at 7%/87%, and Antigravity Gemini at 2%/1% used in 5h/7d. In particular, Haiku's last immediate read was 6% but Claude later reported 7%. See `quota-final.json`; unchanged displayed usage does not establish zero consumption.", "",
    "## Model identity incident and exclusions", "",
    "Two calls requested the `haiku` alias at max, but assistant metadata reported `claude-sonnet-5-5`. The coordinator was interrupted after the in-flight C2 calls completed; no third alias call occurred. Both attempts are preserved and excluded from Haiku and Sonnet-high scores. The five replacement calls use the full `claude-haiku-5-5` identifier and check effective metadata after each case. This makes 27 actual model calls for 25 target cells. Exact cause of alias resolution remains unconfirmed; no global account settings were changed.", "",
    "Official model identifier: [Haiku 5.5 overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview). Supported max effort: [Anthropic effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort). Claude assistant metadata confirms the effective Haiku/Sonnet model IDs. Codex and Gemini record explicit requested IDs; the collector did not retain a provider-confirmed effective ID for them.", "",
    "## Detailed adjudication notes", ""]
for c in data["cells"]:
    if c["note"]:
        lines.append(f"- `{c['record']}`: {c['note']}")
lines += ["", "## Evidence and remaining work", "",
    "`cases.json` contains requirements, plans and the frozen oracle; model prompts use only each case's `input`, never its oracle. `protocol.json`, the two additional protocols and `runtime-versions.json` define invocation conditions. Result JSONs retain final answers, reported usage, hashes, elapsed time and quota, excluding private reasoning text/raw CLI streams. `adjudication.json` and `adjudicate.py` provide the exact manual mapping and calculations. `run.py` and `run_additional.py` reproduce missing cells without rerunning existing records.", "",
    "No product code, Scheduler lifecycle, formal benchmark manifest, reviewer pair, approval state or frozen plan changed. P-109 remains open. The exact T17 Claude Planner isolation check and formal T17–T22 work remain separate. No general quality-parity claim follows from these seeded cases.", ""]
(ROOT / "REPORT.md").write_text("\n".join(lines))
print(ROOT / "REPORT.md")
