"""What earlier attempts of a task tried and how each one failed, for the next attempt's prompt and the owner's card.

A retry used to see only the last verification failure (`RUN.notes/<task>.verify.md`, overwritten each time): not how
many attempts had already failed, nor failures of another kind (a start refused by a clash, a timeout, a cancellation),
nor that the same error kept coming back. REQ-027 T15 ran 13 attempts and T14 hit the same INTEGRATION_CONFLICT three
times. Each verification failure is now appended to `RUN.notes/<task>.history.jsonl` with a signature: its failing
commands and error lines, without numbers, hashes and paths. The other failures are read from M1's attempts. The
prompt lists them oldest first and says plainly when the last ones failed the same way, so the agent changes approach
or reports what blocks it instead of repeating it.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import re
import time
from pathlib import Path

from bitacora_platform import failure_lines

NOTES = "RUN.notes"
SHOWN = 6                   # attempts listed in a prompt; older ones are counted
ERROR_LINE = re.compile(r"error|fail|exit code|cannot|not found|denied|refused|conflict|timeout|assert", re.I)
NOISE = (re.compile(r"\b[0-9a-f]{7,64}\b"), re.compile(r"(?:/[\w.@+-]+)+/"), re.compile(r"\d+(?:\.\d+)?"))


def path(rdir: Path, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.history.jsonl"


def observation_path(rdir: Path, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.audit-observations.jsonl"


def record_observation(rdir: Path, task: str, attempt: str, observation: dict) -> None:
    """Append one complete validated observation; reusing an attempt with different data is refused."""
    if not attempt or not isinstance(observation, dict):
        raise ValueError("invalid audit observation")
    target = observation_path(rdir, task)
    target.parent.mkdir(parents=True, exist_ok=True)
    observation_bytes = json.dumps(observation, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    encoded = json.dumps({"attempt": attempt, "observation": observation,
                          "sha256": hashlib.sha256(observation_bytes).hexdigest()}, sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"))
    try:
        for line in target.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if isinstance(row, dict) and row.get("attempt") == attempt:
                if line != encoded:
                    raise ValueError("audit observation is immutable")
                return
    except FileNotFoundError:
        pass
    with target.open("a", encoding="utf-8") as handle:
        handle.write(encoded + "\n")


def _observations(rdir: Path, task: str) -> list[dict]:
    out = []
    try:
        for line in observation_path(rdir, task).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if isinstance(row, dict) and isinstance(row.get("observation"), dict):
                payload = json.dumps(row["observation"], sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()
                if row.get("sha256") == hashlib.sha256(payload).hexdigest():
                    out.append({"attempt": row.get("attempt"), **row["observation"]})
    except (OSError, ValueError):
        return []
    return out


def signature(text: str) -> str:
    """The same failure gives the same signature across attempts: commands and error lines, without the numbers,
    hashes and paths that change from one attempt to the next."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    keep = [line for line in lines if line.startswith("$ ") or ERROR_LINE.search(line)] or lines[:3]
    norm = []
    for line in keep[:12]:
        for pattern in NOISE:
            line = pattern.sub("#", line)
        norm.append(re.sub(r"\s+", " ", line.lower()))
    return hashlib.sha256("\n".join(norm).encode()).hexdigest()[:12] if norm else ""


def record(rdir: Path, task: str, attempt: str, text: str, kind: str = "verification", *, verdict: str = "") -> None:
    """Append one failure of one attempt (best effort: the history only informs, it never stops a run). `verdict`
    names the verdict the line is about; a second line for the same verdict is not written (a durable verify step that
    runs again after an engine restart returns the stored verdict and reported it once more)."""
    if not text.strip() or not attempt:
        return
    target = path(rdir, task)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            if verdict:
                handle.seek(0)
                for line in handle:
                    try:
                        if json.loads(line).get("verdict") == verdict:
                            return
                    except (ValueError, AttributeError):
                        continue
            row = {"attempt": attempt, "kind": kind, "at": time.time(), "signature": signature(text),
                   "signature_authority": "informational_only", "text": text.strip()}
            if verdict:
                row["verdict"] = verdict
            handle.seek(0, 2)
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _recorded(rdir: Path, task: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    try:
        for line in path(rdir, task).read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("attempt"):
                out[str(row["attempt"])] = row
    except OSError:
        pass
    return out


def entries(rdir: Path, task: str, doc: dict) -> list[dict]:
    """Every settled attempt of the task, oldest first: {attempt, number, outcome, text, signature}."""
    recorded = _recorded(rdir, task)
    out = []
    for number, attempt in enumerate(doc.get("tasks", {}).get(task, {}).get("attempts", []), 1):
        rec = doc.get("attempts", {}).get(attempt, {})
        state = rec.get("state", "")
        if state in ("reserved", "dispatched", "running", "verifying", "uncertain", ""):
            continue
        failure = str(rec.get("failure") or "")
        if state == "accepted":
            outcome, text = "accepted", ""
        elif attempt in recorded:
            outcome, text = "verification failed", recorded[attempt]["text"]
        elif failure.startswith("m6://"):
            outcome, text = "verification failed", "(the failing checks of this attempt were not recorded)"
        else:
            outcome, text = ("cancelled" if state == "cancelled" else "failed"), failure
        out.append({"attempt": attempt, "number": number, "outcome": outcome, "text": text,
                    "signature": recorded.get(attempt, {}).get("signature") or (signature(text) if text else ""),
                    "signature_authority": "informational_only"})
    return out


def with_recorded(doc: dict, rdir: Path, task: str) -> dict:
    """`doc` plus the attempts of `task` that only this history file knows, after the known ones and in the order they
    were recorded, as rejected: a run continued by the durable runtime (REQ-030) keeps one history across both
    runtimes, and a run born there has no M1 document at all."""
    known = list(doc.get("tasks", {}).get(task, {}).get("attempts", []))
    extra = [attempt for attempt in _recorded(rdir, task) if attempt not in known]
    if not extra:
        return doc
    attempts = {**doc.get("attempts", {}), **{attempt: {"state": "rejected", "failure": ""} for attempt in extra}}
    tasks = {**doc.get("tasks", {}), task: {**doc.get("tasks", {}).get(task, {}), "attempts": known + extra}}
    return {**doc, "tasks": tasks, "attempts": attempts}


def repeats(history: list[dict]) -> int:
    """How many of the last failed attempts, counted back from the newest, failed with the same signature."""
    failed = [h for h in history if h["outcome"] != "accepted"]
    if not failed or not failed[-1]["signature"]:
        return 0
    count = 0
    for h in reversed(failed):
        if h["signature"] != failed[-1]["signature"]:
            break
        count += 1
    return count


def _excerpt(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    command = next((line for line in lines if line.startswith("$ ")), "")
    # a verification note opens with advice and a preamble that say "failed": the error is what the check printed under
    # its command, and the decisive line of it (a Playwright timeout matched none of ERROR_LINE's words)
    output = [line for line in (lines[lines.index(command) + 1:] if command else lines) if not line.startswith(("$ ", "exit code"))]
    error = (failure_lines.first_decisive("\n".join(output))
             or next((line for line in output if ERROR_LINE.search(line)),
                     next((line for line in lines if line.startswith("exit code")), "")))
    picked = [x for x in (command, error) if x] or lines[:1]
    return " — ".join(picked)[:300]


def prompt(rdir: Path, task: str, doc: dict) -> str:
    """The section of a retry's prompt about earlier attempts; '' for a first attempt."""
    from bt_prompt_context import concise

    if concise():
        return _concise_prompt(rdir, task, doc)
    history = entries(rdir, task, doc)
    if not history:
        return ""
    observations = doc.get("audit_observations")
    if not isinstance(observations, list) or not observations:
        observations = _observations(rdir, task)
    lines = ["Earlier attempts of this task (oldest first). Read them before you change anything: do not repeat an "
             "approach that already failed."]
    if isinstance(observations, list) and observations:
        lines.append("Structured audit observations (authoritative when validated):")
        for observation in observations:
            if isinstance(observation, dict):
                lines.append("- " + json.dumps(observation, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    hidden = len(history) - SHOWN
    if hidden > 0:
        lines.append(f"- ({hidden} older attempt(s) not shown)")
    seen: dict[str, int] = {}               # signature -> first attempt shown with its text
    for h in history[-SHOWN:]:
        first = seen.get(h["signature"])
        if h["outcome"] == "accepted":
            detail = "accepted, later sent back (rework, audit or plan revision)"
        elif not observations and first is not None and first != h["number"]:
            detail = f"{h['outcome']}: the same failure as attempt #{first}"
        else:
            detail = f"{h['outcome']}: {_excerpt(h['text'])}"
            if h["signature"]:
                seen[h["signature"]] = h["number"]
        lines.append(f"- #{h['number']} {h['attempt']}: {detail}")
    lines.append("Text signatures are heuristic hints only; they are not authoritative evidence of audit recurrence.")
    same = repeats(history)
    if not observations and same >= 2:
        lines.append(f"WARNING: the last {same} attempts failed in exactly the same way. Doing the same again will fail "
                     "again. Find the root cause first; it may be outside the code you wrote (the environment, a "
                     "dependency, the verification command, the plan). If it cannot be fixed within this task, say so "
                     "at the top of your final report, with the evidence, instead of retrying the same change.")
    return "\n".join(lines)


def _concise_prompt(rdir: Path, task: str, doc: dict) -> str:
    history = entries(rdir, task, doc)
    if not history:
        return ""
    observations = doc.get("audit_observations") or _observations(rdir, task)
    lines = ["Earlier attempts of this task (oldest first). Do not repeat failed approaches."]
    if isinstance(observations, list) and observations:
        lines.append("Structured audit observations (authoritative when validated):")
        lines.extend("- " + json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                     for o in observations if isinstance(o, dict))
    groups: dict[tuple[str, str], list[dict]] = {}
    for entry in history:
        groups.setdefault((entry["outcome"], entry["text"]), []).append(entry)
    keep = {h["attempt"] for group in groups.values() for h in (group[0], group[-1])}
    for entry in history:
        group = groups[(entry["outcome"], entry["text"])]
        if entry["attempt"] not in keep:
            continue
        header = f"- #{entry['number']} {entry['attempt']}: {entry['outcome']}"
        if entry["outcome"] == "accepted":
            lines.append(header + ", later sent back (rework, audit or plan revision)")
            continue
        if entry is group[0] and len(group) > 1:
            header += f"; same failure ×{len(group)} (first/latest text; attempts " + ", ".join(h["attempt"] for h in group) + ")"
        lines.append(header + ": " + entry["text"])
    lines.append("Text signatures are heuristic hints only; they are not authoritative evidence of audit recurrence.")
    if not observations and len(history) > 1 and history[-1]["outcome"] != "accepted":
        last = history[-1]
        count = 0
        for entry in reversed(history):
            if (entry["outcome"], entry["text"]) != (last["outcome"], last["text"]):
                break
            count += 1
        if count > 1:
            lines.append(f"WARNING: the last {count} attempts have identical failure text. Find the root cause; "
                         "if outside this task, report the blocker with evidence.")
    return "\n".join(lines)
