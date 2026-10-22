"""Coordinator attestations: a receipt for a manual verification check (REQ-030 step 4).

Some criteria cannot be proven by a command in a sandbox: a flow on a real phone, a live deployment, a service only the
owner can reach. The plan declares them as `manual` checks and the verifier used to stop and ask a person every time,
although the coordinator (the HQ session or the owner) had already done the check. A receipt makes that evidence
verifiable instead of verbal:

- it is bound to WHAT is attested: task, check purpose, check value and expected text. Change the check or the criterion and
  the receipt no longer applies;
- it carries the evidence the coordinator wrote (what was done, what was seen), who attested and when;
- it is sealed with an HMAC under a key kept in the machine's state directory (mode 0600), so a file edited by hand or copied
  from another check does not verify.

The verifier asks `lookup(rdir)(order, spec)`; a valid receipt settles ONLY that manual check. Command checks of the same
criterion still have to pass. The receipt's digest goes into the verification evidence, so the audit trail shows that a
person-free pass rested on an attestation and which one.

Honest limit: the key sits on the same machine as the agents. The seal protects against edits and mix-ups, not against an
agent with full filesystem access that sets out to forge it; the evidence text and the run's audit trail are what a review
checks. `scheduler-op REQ attest TASK` is the only supported way to mint one.

Key rotation (`bitacora.py attestation-key rotate`): a new key seals from then on and the previous one is kept as
`attestation.key.prev`, so receipts already minted still verify for one generation; a second rotation drops it, and every
receipt sealed under it stops verifying (the task asks for its manual check again). Rotate when the key may have leaked (a
copy of the state directory left the machine); `attestation-key status` shows when each key was written.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

SCHEMA = "attestation/1"
DIR = "RUN.attestations"
MIN_EVIDENCE = 20


class AttestationError(ValueError):
    pass


def key_path() -> Path:
    from bt_core import STATE

    return Path(STATE) / "attestation.key"


def _key(path: Path | None = None, *, create: bool = False) -> bytes | None:
    path = path or key_path()
    try:
        key = path.read_bytes()
        if len(key) >= 32:
            return key                      # a shorter file is a damaged key (an empty one would seal anything): never used
    except OSError:
        pass
    if not create:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:                 # another minter was first, or the file is damaged: replace a damaged one
        if len(path.read_bytes()) >= 32:
            return path.read_bytes()
        path.write_bytes(os.urandom(32))
        os.chmod(path, 0o600)
        return path.read_bytes()
    try:
        os.write(fd, os.urandom(32))
    finally:
        os.close(fd)
    return path.read_bytes()


def _previous(path: Path) -> Path:
    return path.with_name(path.name + ".prev")


def _keys(path: Path | None = None) -> list[bytes]:
    """The current key, then the one before the last rotation (receipts sealed under it still verify)."""
    path = path or key_path()
    keys: list[bytes] = []
    for candidate in (path, _previous(path)):
        try:
            key = candidate.read_bytes()
        except OSError:
            continue
        if len(key) >= 32:
            keys.append(key)
    return keys


def rotate(key_file: Path | None = None) -> Path:
    """A new key from now on; the one it replaces stays as `.prev` for one generation. Returns the key's path."""
    path = key_file or key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_bytes() if path.is_file() else b""
    if len(current) >= 32:
        previous = _previous(path)
        fd = os.open(previous, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, current)
        finally:
            os.close(fd)
    fresh = path.with_name(path.name + ".new")
    fd = os.open(fresh, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, os.urandom(32))
    finally:
        os.close(fd)
    os.replace(fresh, path)
    return path


def key_status(key_file: Path | None = None) -> list[str]:
    path = key_file or key_path()
    lines = []
    for label, candidate in (("current", path), ("previous", _previous(path))):
        try:
            usable = len(candidate.read_bytes()) >= 32
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(candidate.stat().st_mtime))
            lines.append(f"{label}: {candidate} ({'valid' if usable else 'DAMAGED'}, written {when}, mode {oct(candidate.stat().st_mode & 0o777)})")
        except OSError:
            lines.append(f"{label}: none")
    return lines


def binding(task_id: str, purpose: str, value: str, expected: str = "", attempt: str = "") -> str:
    """What a receipt is about, as one digest. A receipt bound to an attempt (REQ-029 A11) covers only the work that attempt
    produced: a redone task needs a new attestation. Without an attempt the digest is the original one."""
    parts = [task_id, purpose, value, expected] + ([attempt] if attempt else [])
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def receipt_path(rdir: Path | str, task_id: str, bound: str) -> Path:
    return Path(rdir) / DIR / re.sub(r"[^A-Za-z0-9._-]", "_", task_id) / f"{bound[:16]}.json"


def _seal(body: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, json.dumps(body, sort_keys=True, ensure_ascii=False).encode(), hashlib.sha256).hexdigest()


def mint(rdir: Path | str, task_id: str, purpose: str, value: str, expected: str, evidence: str, by: str,
         *, attempt: str = "", key_file: Path | None = None, now: Callable[[], float] = time.time) -> Path:
    """Write the receipt for one manual check. `evidence` says what was done and seen (at least a sentence)."""
    evidence = (evidence or "").strip()
    if len(evidence) < MIN_EVIDENCE:
        raise AttestationError(f"an attestation needs the evidence in words (at least {MIN_EVIDENCE} characters): what was "
                               "done and what was seen")
    if not by.strip():
        raise AttestationError("an attestation names who attests")
    bound = binding(task_id, purpose, value, expected, attempt)
    body = {"schema": SCHEMA, "task": task_id, "purpose": purpose, "value": value, "expected": expected,
            **({"attempt": attempt} if attempt else {}), "binding": bound, "by": by.strip(), "at": round(now(), 3), "evidence": evidence[:4000],
            "evidence_sha256": hashlib.sha256(evidence.encode()).hexdigest()}
    body["seal"] = _seal({k: v for k, v in body.items() if k != "seal"}, _key(key_file, create=True))
    path = receipt_path(rdir, task_id, bound)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def verify(rdir: Path | str, task_id: str, purpose: str, value: str, expected: str = "",
           *, attempt: str = "", key_file: Path | None = None) -> str | None:
    """`sha256:<digest of the receipt file>` when a valid receipt holds for exactly this check (and, when `attempt` is given,
    for exactly that attempt), else None."""
    bound = binding(task_id, purpose, value, expected, attempt)
    path = receipt_path(rdir, task_id, bound)
    keys = _keys(key_file)
    try:
        raw = path.read_bytes()
        body = json.loads(raw)
    except (OSError, ValueError):
        return None
    if not keys or not isinstance(body, dict) or body.get("schema") != SCHEMA or body.get("binding") != bound:
        return None
    seal = body.get("seal")
    unsealed = {k: v for k, v in body.items() if k != "seal"}
    if not isinstance(seal, str) or not any(hmac.compare_digest(seal, _seal(unsealed, key)) for key in keys):
        return None
    if body.get("task") != task_id or body.get("purpose") != purpose or body.get("attempt", "") != attempt or len(str(body.get("evidence", "")).strip()) < MIN_EVIDENCE:
        return None
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def lookup(rdir: Path | str, *, bind_attempt: bool = False, key_file: Path | None = None
           ) -> Callable[[Any, Any], str | None]:
    """The port the verifier is given: (order, check spec) -> receipt digest or None. With `bind_attempt` a receipt counts only
    for the attempt the order verifies (`gates.attestation_bind_attempt`)."""
    def find(order, spec) -> str | None:
        return verify(rdir, order.task_id, spec.purpose, spec.command, spec.expected,
                      attempt=order.attempt_id if bind_attempt else "", key_file=key_file)
    return find


def manual_checks(plan, task_id: str) -> list[dict[str, str]]:
    """The manual checks a plan task declares: [{purpose, value, expected}]."""
    return [{"purpose": str(v.get("purpose", "")), "value": str(v.get("value", "")), "expected": str(v.get("expected", ""))}
            for v in plan.task(task_id).verification if v.get("type") == "manual"]
