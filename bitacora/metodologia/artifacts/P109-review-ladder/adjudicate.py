"""Explicit coordinator adjudication against the oracle frozen before calls.

No model grades another model. Human-readable mapping is intentionally explicit;
test-coverage restatements are counted once with their implementation root cause.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
cases = {c["id"]: c for c in json.loads((ROOT / "cases.json").read_text())}
protocol = json.loads((ROOT / "protocol.json").read_text())
assert hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest() == protocol["oracle_sha256"]

# Index entries: positive N maps the finding to oracle defect DN; zero means
# duplicate coverage observation; None means an unconfirmed additional concern.
MAPS = {
    "C1-codex-2": [1, 2], "C1-claude-work": [2, 1, 0, None], "C1-antigravity": [1, 2, 0],
    "C2-codex-2": [1, 2, 3], "C2-claude-work": [1, 2, 3], "C2-antigravity": [1, 2, 3],
    "C3-codex-2": [1, 2, 3, 4], "C3-claude-work": [1, 2, 3, 4, None],
    "C3-antigravity": [1, 0, 2, 0, 3, 0, 4, None],
    "C4-codex-2": [4, 1, 2, 3, 5], "C4-claude-work": [4, 1, 2, 3, 5, 0],
    "C4-antigravity": [4, 1, 2, 3, 5, 0],
    "C5-codex-2": [1, 2, 3, 4, 5, 6], "C5-claude-work": [1, 2, 3, 4, 5, 6, 0],
    "C5-antigravity": [1, 2, 3, 4, 5, 6],
    "C1-codex-2-luna": [1, 2, 0], "C2-codex-2-luna": [1, 2, 3],
    "C1-claude-work-haiku55": [1, 2, 0, 0, None, 0],
    "C2-claude-work-haiku55": [1, 2, 3, None],
    "C3-codex-2-luna": [1, 2, 3, 4],
    "C3-claude-work-haiku55": [1, 2, 4, 3, None],
    "C4-codex-2-luna": [4, 1, 2, 3, 5, 0],
    "C4-claude-work-haiku55": [1, 2, 5, 3, 4, 0, None],
    "C5-codex-2-luna": [1, 2, 3, 4, 5, None, 6],
    "C5-claude-work-haiku55": [2, 1, 3, 4, 5, 6, 0, None],
}
NOTES = {
    "C1-claude-work": "Finding 4 raises missing HTTP-400 translation, but the supplied parser contract does not establish its error signaling or the existing HTTP translation. Track as unconfirmed, not a proven false positive or an additional proven defect.",
    "C2-claude-work": "The cycle is proven. The extra claim that snapshot-after-DTO is intrinsically semantically wrong is not established; it is not needed to establish the cycle.",
    "C3-claude-work": "Finding 5 proposes pre-cutover validation ordering. The mission does not explicitly require T6 before T5, and T5 has its own verification period; retain as an unconfirmed planning concern.",
    "C3-antigravity": "Findings 2/4/6 restate coverage for existing roots. Finding 8 is the same unconfirmed pre-cutover gate concern as Sonnet. The title says unvalidated tenant, but the evidence correctly distinguishes UUID validation from missing authorization.",
    "C5-claude-work": "Output contains two JSON documents plus prose and 1105 whitespace-delimited words. Content recovery is for manual scoring only, never a successful machine contract. Finding 7 restates verification coverage and adds an unproven task-order concern. Its claim that reservations can change while BEGIN IMMEDIATE holds the write transaction is incorrect under the stated database locking; the network-in-transaction defect remains correct.",
    "C5-antigravity": "All six roots are correct. The stale-quota scenario overstates execution impact: baseline M1 correctly revalidates at dispatch, so the evidence establishes a bad M2 recommendation, not that a depleted-provider call necessarily occurs.",
    "C1-claude-work-haiku55": "Findings 3/4 restate tests for the two roots. Finding 5 assumes the named tenant isolation test has no foreign-tenant fixture, which is not established. Finding 6 repeats coverage and treats unspecified HTTP assertions as missing; the invalid-input tests are already named. Track these caveats without inventing additional proven defects.",
    "C2-claude-work-haiku55": "Finding 4 raises unspecified API deployment ordering. The task ordering and staged deployment facts do not prove the API will ship before the database migration; track as an unconfirmed plan concern. Sonnet raised the same point as an uncertainty, rather than as a finding.",
    "C3-claude-work-haiku55": "Finding 5 raises the same unconfirmed T6-before-cutover concern as Sonnet/Gemini, adding a rollback rehearsal proposal. The predeclared defects already account for the broken rollback. The optional trigger/canary uncertainties are not counted as findings.",
    "C4-claude-work-haiku55": "Finding 6 repeats coverage for seeded roots. Finding 7 raises rollback draining and the 72-hour retry boundary; whether the disabled new worker includes the outbox dispatcher, or jobs will be retried after 72h, is not specified. Retain as an unconfirmed concern, not a false positive. The generation finding also proposes provider-path ordering beyond the demonstrated finalization defect.",
    "C5-codex-2-luna": "Finding 6 correctly observes that the T5 revalidation list does not explicitly name the required budget check. This is a useful additional traceability concern outside the predeclared oracle. As with the HTTP-400 translation concern, omitted plan text does not prove an existing runtime guard is absent; retain separately from the 20 proven seeded defects, without silently expanding the frozen denominator or declaring the observation false.",
    "C5-claude-work-haiku55": "All six planted roots are found. Finding 7 duplicates their test coverage; finding 8 is the same budget traceability concern as Luna, with an explicit uncertainty about budget versus quota. Two auxiliary claims are incorrect: the contract does define fresh quota, and the baseline explicitly guarantees v1 preservation. The overwritten startup map is defective, but claiming it necessarily mutates v1 evidence contradicts that baseline.",
}


def recovered_answer(record):
    if isinstance(record.get("answer"), dict):
        return record["answer"], False
    answers = []
    for m in re.finditer(r'\{\s*"verdict"', record.get("response_text", "")):
        try:
            answer, _ = json.JSONDecoder().raw_decode(record["response_text"][m.start():])
        except ValueError:
            continue
        if isinstance(answer, dict) and isinstance(answer.get("findings"), list):
            answers.append(answer)
    return (answers[-1], True) if answers else (None, False)


def usage_totals(record):
    usage = record.get("usage_reported", {})
    if record["provider"] == "claude":
        input_tokens = sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        cached = usage.get("cache_read_input_tokens", 0)
        thinking = usage.get("output_tokens_details", {}).get("thinking_tokens")
    else:
        input_tokens = usage.get("input_tokens", 0)
        cached = usage.get("cached_input_tokens", usage.get("cache_read_tokens", 0))
        thinking = usage.get("reasoning_output_tokens", usage.get("thinking_tokens"))
    output = usage.get("output_tokens", 0)
    return {"input_including_cache": input_tokens, "cached_read_input": cached,
            "output_including_thinking": output, "thinking_subset": thinking,
            "total_tokens": input_tokens + output}


cells = []
for key, mapping in MAPS.items():
    record = json.loads((ROOT / f"{key}.json").read_text())
    case = cases[record["case"]]
    prompt = protocol["instruction"] + case["input"]
    assert hashlib.sha256(prompt.encode()).hexdigest() == record["prompt_sha256"], key
    answer, recovered = recovered_answer(record)
    assert answer and len(answer["findings"]) == len(mapping), key
    assert record["status"] == "completed" and record["observed_tool_events"] == 0, key
    detected = sorted({f"{case['id']}-D{n}" for n in mapping if n})
    expected = {d["id"] for d in case["oracle"]}
    assert set(detected) <= expected
    words = len(record.get("response_text", "").split())
    cell = {"record": key + ".json", "case": case["id"], "profile": record["profile"],
            "requested_model": record["requested_model"], "requested_effort": record["requested_effort"],
            "detected": detected, "expected": len(expected), "missed": sorted(expected - set(detected)),
            "finding_map": mapping, "duplicates": mapping.count(0), "unconfirmed_concerns": mapping.count(None),
            "content_recovered_only_for_manual_scoring": recovered,
            "automatically_usable": record["format_valid"] and words <= 900,
            "response_words": words, "elapsed_seconds": record["elapsed_seconds"],
            "tokens": usage_totals(record), "note": NOTES.get(key, "")}
    cells.append(cell)
summaries = []
for model in dict.fromkeys(c["requested_model"] for c in cells):
    group = [c for c in cells if c["requested_model"] == model]
    records = [json.loads((ROOT / c["record"]).read_text()) for c in group]
    totals = {k: sum(c["tokens"][k] or 0 for c in group) for k in group[0]["tokens"]}
    detected = sum(len(c["detected"]) for c in group)
    total_time = round(sum(c["elapsed_seconds"] for c in group), 3)
    uncertain = sum(c["unconfirmed_concerns"] for c in group)
    recall = detected / sum(c["expected"] for c in group)
    precision_lower = detected / (detected + uncertain) if detected else 0
    f1_lower = 2 * precision_lower * recall / (precision_lower + recall) if precision_lower + recall else 0
    f1_upper = 2 * recall / (1 + recall)
    summaries.append({"model": model, "effort": group[0]["requested_effort"], "cases": len(group),
        "detected": detected, "expected": sum(c["expected"] for c in group),
        "automatically_usable_cases": sum(c["automatically_usable"] for c in group),
        "duplicates": sum(c["duplicates"] for c in group),
        "unconfirmed_concerns": uncertain,
        "recall": recall, "precision_bounds": [precision_lower, 1.0], "f1_bounds": [f1_lower, f1_upper],
        "elapsed_seconds_sum": total_time, "tokens": totals,
        "tokens_per_detected_defect": round(totals["total_tokens"] / detected, 1) if detected else None,
        "seconds_per_detected_defect": round(total_time / detected, 2) if detected else None,
        "quota_before_first": records[0]["quota_before"], "quota_after_last": records[-1]["quota_after"]})
result = {"schema_version": 1, "method": "Explicit coordinator mapping against predeclared oracle; one run per cell; no independent formal benchmark grading",
          "oracle_sha256": protocol["oracle_sha256"], "cells": cells, "summaries": summaries,
          "precision_policy": "Unconfirmed additional concerns are not automatically false positives. Report conservative/optimistic precision and F1 bounds: the lower bound treats each as unsupported, the upper bound treats each as valid. Duplicates are excluded from both numerator and denominator. These are descriptive scores, not statistical confidence intervals. Incorrect auxiliary statements are documented separately from otherwise correct root findings.",
          "excluded": ["C1-claude-work-haiku.json", "C2-claude-work-haiku.json"]}
(ROOT / "adjudication.json").write_text(json.dumps(result, indent=2) + "\n")
for s in summaries:
    print(s["model"], f"{s['detected']}/{s['expected']}", f"format={s['automatically_usable_cases']}/{s['cases']}", s["tokens"], s["elapsed_seconds_sum"])
