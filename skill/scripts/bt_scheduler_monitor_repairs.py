"""Narrow, evidence-bound repairs authorized for the Pictures REQ-021 monitor."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import bt_run_stores
import bt_scheduler_decisions as decisions
import bt_scheduler_ops as ops

MARKER = "OWNER_MONITOR_ACTIVATION_LABEL"
NOTE = (MARKER + ": The independent M6 check got past the production build but timed out at "
        "getByLabel('Contraseña nueva'). The activation form in the tested snapshot labels it 'Nueva contraseña' "
        "and chooses Spanish or English from the browser Accept-Language. Diagnose the real activation page and "
        "redirects, explicitly set the browser context locale for this Spanish test, and use the actual accessible "
        "labels. Preserve the real browser, database, activation, login and authorization assertions. Add a "
        "regression and run the original integration check with the authorized disposable test database; do not "
        "weaken the test or expose credentials. Preserve the isolated HOME fix.")


def activation_failure(rdir: Path, request: str, attempt: str) -> bool:
    path = bt_run_stores.paths(rdir).get("m6")
    if path is None:
        return False
    with closing(sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True, timeout=2)) as db:
        row = db.execute("SELECT result_json,result_hash FROM requests WHERE idempotency_key=?", (request,)).fetchone()
        if not row or not row[0] or hashlib.sha256(row[0].encode()).hexdigest() != row[1]:
            return False
        result = json.loads(row[0])
        if result.get("status") != "FAIL" or result.get("identity", {}).get("attempt_id") != attempt:
            return False
        for check in result.get("checks", []):
            if check.get("status") != "fail" or check.get("command") != "npm run cuentas:test-integracion-ui":
                continue
            ref = check.get("stderr_ref", "")
            digest = ref.removeprefix("m6://artifact/") if ref.startswith("m6://artifact/") else ""
            artifact = db.execute("SELECT content FROM artifacts WHERE digest=?", (digest,)).fetchone()
            if artifact and hashlib.sha256(artifact[0]).hexdigest() == digest:
                return b"locator.fill: Timeout" in artifact[0] and b"Contrase\xc3\xb1a nueva" in artifact[0]
    return False


def repair_once(project: str, req: str, rdir: Path, status: dict) -> str | None:
    if (project, req) != ("pictures", "REQ-021") or status.get("owner_pids") or status.get("live_attempts") or status.get("hold"):
        return None
    state = decisions._state(rdir)
    task = state.get("tasks", {}).get("T2.6", {})
    attempts = task.get("attempts", [])
    if task.get("state") != "blocked" or not attempts:
        return None
    answers = decisions.answers_path(rdir)
    if answers.exists() and MARKER in answers.read_text(encoding="utf-8"):
        return None
    attempt = attempts[-1]
    request = f"{req}:r{state['revision']}:{attempt}:verify"
    if not activation_failure(rdir, request, attempt):
        return None
    cards = [card for card in decisions.open_requests(rdir) if card.get("task") == "T2.6" and card.get("source") == "task"]
    if len(cards) != 1:
        return None
    with ops.hold(rdir, "bounded monitor repair for activation label") as token:
        now = ops.status(project, req, rdir)
        if now.get("owner_pids") or now.get("live_attempts") or not ops.owns_hold(rdir, token):
            return None
        decisions.answer(project, req, rdir, cards[0]["id"], "retry_with_note", NOTE, by="scheduler")
    return f"T2.6 reopened once for verified activation-label failure ({attempt})"
