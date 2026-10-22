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


def _state(finding: Mapping[str, Any]) -> str:
    return "open" if finding["status"] == "open" else ("fixed" if finding["status"] == "fixed" else "accepted")


def compare(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    """Progress from one audit ledger to the next: persisted / fixed / new / regressed / uncertain (occurrence ids) plus how each
    relation was decided. Same vocabulary and rules as the M5 `assess_progress` (a related finding persists, is fixed or
    regressed; an unrelated one is fixed (already marked so) or new; an open finding nobody relates to is uncertain)."""
    old, new = list(previous["findings"]), list(current["findings"])
    pairs = sorted(((score(o, n), o["id"], n["id"]) for o in old for n in new), reverse=True)
    used_old: set[str] = set()
    used_new: set[str] = set()
    strong: dict[str, str] = {}                              # current id -> previous id
    weak: dict[str, tuple[str, float]] = {}
    for value, o_id, n_id in pairs:
        if o_id in used_old or n_id in used_new or value < WEAK:
            continue
        used_old.add(o_id)
        used_new.add(n_id)
        if value >= STRONG:
            strong[n_id] = o_id
        else:
            weak[n_id] = (o_id, value)
    by_old = {f["id"]: f for f in old}
    cur, prev = current["ledger_sha256"], previous["ledger_sha256"]
    groups: dict[str, list[str]] = {"persisted": [], "fixed": [], "new": [], "regressed": [], "uncertain": []}
    why: dict[str, dict] = {}
    for finding in new:
        key = f"{cur}:{finding['id']}"
        if finding["id"] in weak:
            groups["uncertain"].append(key)
            why[key] = {"previous": weak[finding["id"]][0], "score": weak[finding["id"]][1], "decision": "uncertain: weak evidence"}
        elif finding["id"] in strong:
            before = by_old[strong[finding["id"]]]
            why[key] = {"previous": before["id"], "score": score(before, finding), "decision": "related"}
            if _state(before) == "fixed" and _state(finding) == "open":
                groups["regressed"].append(key)
            elif _state(finding) == "fixed":
                groups["fixed"].append(key)
            else:
                groups["persisted"].append(key)
        else:
            groups["fixed" if _state(finding) == "fixed" else "new"].append(key)
    matched = {*strong.values(), *(o for o, _ in weak.values())}
    groups["uncertain"] += [f"{prev}:{f['id']}" for f in old if _state(f) == "open" and f["id"] not in matched]
    groups = {k: sorted(set(v)) for k, v in groups.items()}
    return {**groups, "relations": why, "counts": {"previous": len(old), "current": len(new)}}


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
