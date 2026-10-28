"""A disposable bitácora root that the real remote producers (`bt_remote_snapshot`, `bt_remote_events`,
`bt_remote_api`) read: one Scheduler run with a live, a rejected and a failed task, its frozen plan, an open question
round and one open decision request. Stdlib only, so both the stdlib suite and the Pydantic contract tests use it."""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

STAMP = dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.UTC).timestamp()

# What bt_scheduler_decisions.open_requests returns for a blocked task: bt_plans_api.open_decisions then adds the
# page-only `diagnosis_html` and `note_prefill`, which the remote snapshot must not forward.
DECISION = {
    "needs": "Decidir si se reintenta.", "you_can": ["Reintenta con una nota."], "error": "Último fallo: tests failed",
    "id": "T3:1", "source": "task", "task": "T3", "attempt": "A-failed", "title": "T3 bloqueada: attempts_exhausted",
    "what": "Se agotaron los intentos.", "reason": "attempts_exhausted", "evidence": ["intentos: 1"],
    "options": [{"id": "retry", "label": "Reintentar", "consequence": "Un intento nuevo."},
                {"id": "rework_conflict", "target": ["T3"], "label": "Devolver T3", "consequence": "Rehace T3."},
                {"id": "stop", "label": "Detener el run", "consequence": "Para el scheduler."}],
    "recommended": "retry", "unskippable": False, "project": "demo", "req": "REQ-001",
    "diagnosis": {"kind": "rule", "label": "reglas", "tone": "warn", "headline": "Fallan los tests",
                  "origin": "<b>tests</b>", "steps": ["mira"], "confidence": "media", "option": "retry"},
    "agent": None,
}


def build(root: Path) -> Path:
    """Write the run under `root` and return its requirement directory."""
    import bt_rounds
    import bt_scheduler_adapter as scheduler_adapter

    base = Path(root).resolve()
    rdir = base / "demo" / "requirements" / "REQ-001-fixture"
    rdir.mkdir(parents=True)
    tasks = [{"id": "T1", "milestone_id": "M1", "title": "Active task", "after": [], "complexity": "low",
              "acceptance_criteria": ["Active work is visible"]},
             {"id": "T2", "milestone_id": "M1", "title": "Rejected task", "after": [], "complexity": "low"},
             {"id": "T3", "milestone_id": "M1", "title": "Failed task", "after": [], "complexity": "low"}]
    plan = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
            "milestones": [{"id": "M1", "title": "First"}], "tasks": tasks}
    (rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
    (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-001 — Fixture\n", encoding="utf-8")
    (rdir / "SPEC.md").write_text("# Spec — REQ-001 — Fixture\n", encoding="utf-8")
    db = scheduler_adapter.run_db_path(rdir)
    db.parent.mkdir(parents=True)
    doc = {"tasks": {"T1": {"state": "active", "attempts": ["A-live"]},
                     "T2": {"state": "recovering", "attempts": ["A-rejected"]},
                     "T3": {"state": "blocked", "attempts": ["A-failed"]}},
           "attempts": {"A-live": {"id": "A-live", "task_id": "T1", "number": 1, "state": "running",
                                    "created_at": STAMP - 60, "updated_at": STAMP, "last_event_at": STAMP},
                        "A-rejected": {"id": "A-rejected", "task_id": "T2", "number": 1, "state": "rejected",
                                       "created_at": STAMP - 120, "updated_at": STAMP - 30,
                                       "failure": "review required"},
                        "A-failed": {"id": "A-failed", "task_id": "T3", "number": 1, "state": "failed",
                                     "created_at": STAMP - 120, "updated_at": STAMP - 30,
                                     "failure": "tests failed; API_KEY=sk-synthetic-not-a-secret-0123456789"}}}
    connection = sqlite3.connect(db)
    try:
        with connection:
            connection.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
            connection.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
    finally:
        connection.close()
    projection = {"authority": "scheduler", "projection": True, "req": "REQ-001", "status": "running",
                  "heartbeat_at": dt.datetime.now(dt.UTC).isoformat(),
                  "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "a" * 64},
                  "tasks": [{"id": "T1", "title": "Active task", "status": "in_progress", "scheduler_state": "active",
                             "attempts": 1},
                            {"id": "T2", "title": "Rejected task", "status": "in_progress",
                             "scheduler_state": "recovering", "attempts": 1},
                            {"id": "T3", "title": "Failed task", "status": "blocked", "scheduler_state": "blocked",
                             "attempts": 1, "attempts_used": 1, "max_attempts": 1, "retries_remaining": 0,
                             "retry_exhausted": True, "reason": "attempts_exhausted"}]}
    (rdir / "RUN.projection.json").write_text(json.dumps(projection), encoding="utf-8")
    bt_rounds.new_round(rdir, {"title": "Scope", "intro": "Confirm the scope.", "coverage": "1/2", "questions": [
        {"id": "q1", "text": "Which priority?", "type": "choice", "options": [{"key": "a", "label": "Fast"}],
         "recommended": "a", "why": "Safer.", "agent_note": "free-form key the snapshot must not forward"},
        {"id": "q2", "text": "Anything else?", "suggested": "No"}]})
    return rdir


@contextlib.contextmanager
def producing(root: Path):
    """Point the producers at `root` with fresh shared caches and the fixture's open decision."""
    import bt_core
    import bt_live_api as live

    base = Path(root).resolve()
    live._now_data_cache.pop(base, None)
    live._now_cache.pop(base, None)
    with patch.object(bt_core, "ROOT", base), \
            patch("bt_scheduler_decisions.open_requests", side_effect=lambda _rdir: [json.loads(json.dumps(DECISION))]):
        yield base
    live._now_data_cache.pop(base, None)
    live._now_cache.pop(base, None)
