"""Read-only history preview of a repeated audit (REQ-029 R2/R3, T11): which findings persisted, were fixed, are new or came back.

Finding numbers are local to one ledger (`F3` of round 1 is not `F3` of round 2), so findings are related by evidence, never by
number: the owner tasks they name and the words of their summaries. A relation is made only above a threshold; a weaker one is
reported as UNCERTAIN, never promoted. A finding that disappears without a `fixed` status is uncertain too (the count alone proves
nothing). The result goes through the isolated M5 `assess_progress`, so the vocabulary is the one the recovery cycle uses.

Pure: nothing is written, no model is invoked, no run is touched. `coverage_gaps` compares the paths an attempt changed with the
commands it carried, with the same rule the verifier applies (`bt_recovery_evidence._command_covers_path`).
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from bt_scheduler_recovery.diagnostic_contracts import FindingOccurrence, FindingRelation, ProgressSnapshot
from bt_scheduler_recovery.progress import assess_progress

STRONG, WEAK = 0.45, 0.25
STOP = frozenset("""still that with this from have does without into their there which when then than been were also only more
most must each other another because before after while whose about above below under over such same both just like some none""".split())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z0-9_]{3,}", text.lower()) if w not in STOP}


def score(previous: Mapping[str, Any], current: Mapping[str, Any]) -> float:
    """0..1 evidence that two findings are the same defect: shared owner tasks (40 %) and shared words (60 %); the same owners plus a shared subject is a strong anchor."""
    a, b = _words(str(previous.get("summary", ""))), _words(str(current.get("summary", "")))
    words = len(a & b) / len(a | b) if a | b else 0.0
    ta, tb = set(previous.get("tasks") or ()), set(current.get("tasks") or ())
    tasks = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    value = 0.6 * words + 0.4 * tasks
    if ta and ta == tb and words >= 0.12:          # the very same owners and a shared concrete subject: a strong anchor
        value = max(value, STRONG + 0.01)
    return round(value, 3)


def _occurrence(ledger: Mapping[str, Any], finding: Mapping[str, Any]) -> FindingOccurrence:
    digest = str(ledger["ledger_sha256"])
    return FindingOccurrence(digest, str(finding["id"]), "open" if finding["status"] == "open" else
                             ("fixed" if finding["status"] == "fixed" else "accepted"), (f"ledger:{digest}",))


def compare(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    """Progress from one audit ledger to the next: persisted / fixed / new / regressed / uncertain (occurrence ids) plus how each
    relation was decided."""
    old = [f for f in previous["findings"]]
    new = [f for f in current["findings"]]
    pairs = sorted(((score(o, n), o["id"], n["id"]) for o in old for n in new), reverse=True)
    used_old: set[str] = set()
    used_new: set[str] = set()
    relations, weak, why = [], [], {}
    for value, o_id, n_id in pairs:
        if o_id in used_old or n_id in used_new or value < WEAK:
            continue
        used_old.add(o_id)
        used_new.add(n_id)
        if value >= STRONG:
            relations.append((o_id, n_id, value))
        else:
            weak.append((o_id, n_id, value))
    prev_snap = [_occurrence(previous, f) for f in old]
    cur_snap = [_occurrence(current, f) for f in new]
    links = tuple(FindingRelation(f"{previous['ledger_sha256']}:{o}", f"{current['ledger_sha256']}:{n}", "same_finding",
                                  (f"ledger:{current['ledger_sha256']}",)) for o, n, _ in relations)
    progress = assess_progress(ProgressSnapshot(tuple(prev_snap)), ProgressSnapshot(tuple(cur_snap), links))
    for o, n, value in relations:
        why[f"{current['ledger_sha256']}:{n}"] = {"previous": o, "score": value, "decision": "related"}
    for o, n, value in weak:
        why[f"{current['ledger_sha256']}:{n}"] = {"previous": o, "score": value, "decision": "uncertain: weak evidence"}
    uncertain = sorted({*progress.uncertain, *(f"{current['ledger_sha256']}:{n}" for _, n, _ in weak)})
    # a weak match is neither persistence nor novelty: it leaves the "new" list and waits for a person
    def keep(ids):
        return [i for i in ids if i not in uncertain]
    return {"persisted": keep(progress.persisted), "fixed": keep(progress.fixed), "new": keep(progress.new),
            "regressed": keep(progress.regressed), "uncertain": uncertain, "relations": why,
            "counts": {"previous": len(old), "current": len(new)}}


def label(ledger: Mapping[str, Any], occurrence: str) -> str:
    finding_id = occurrence.split(":", 1)[1]
    found = next((f for f in ledger["findings"] if f["id"] == finding_id), {})
    return str(found.get("summary", ""))


def history(rounds: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compare every consecutive pair of ledgers; the digest binds the answer to the exact ledgers read."""
    steps = [{"from": a["round"], "to": b["round"], **compare(a, b)} for a, b in zip(rounds, rounds[1:])]
    body = {"schema_version": "recovery-history-preview/1", "steps": steps,
            "ledgers": [{"round": r["round"], "attempt": r.get("attempt"), "ledger_sha256": r["ledger_sha256"],
                         "findings": len(r["findings"])} for r in rounds],
            "diagnosis_invoked": False, "writes": 0}
    body["digest"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return body


def coverage_gaps(attempt: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Changed paths that no carried command runs anything over (a backend-only check on a changed web page)."""
    from bt_recovery_evidence import _command_covers_path

    return [{"attempt": attempt.get("attempt"), "task": attempt.get("task"), "path": path,
             "reason": "no carried check runs over this changed surface"}
            for path in attempt.get("changed_paths", ())
            if not any(_command_covers_path(path, command) for command in attempt.get("checks", ()))]
