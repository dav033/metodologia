"""Question rounds and plan review as files, so any agent (Claude, Codex) and the local web server share them.

Round file: requirements/REQ-NNN-<slug>/rounds/round-NN.json
{
  "round": 2, "title": "Scope & users", "intro": "...", "coverage": "4/10",
  "questions": [
    {"id": "q1", "text": "...", "type": "choice", "options": [{"key": "a", "label": "..."}],
     "recommended": "a", "why": "..."},
    {"id": "q2", "text": "...", "type": "open", "suggested": "...", "why": "..."}
  ],
  "status": "open" | "answered",
  "answers": {"q1": {"choice": "a", "note": ""}, "q2": {"text": "..."}},
  "answered_at": "...", "answered_via": "web" | "terminal"
}
"""
from __future__ import annotations

import time

from bt_core import *  # noqa: F403
from bt_core import _front


def rounds_dir(rdir: Path) -> Path:
    return rdir / "rounds"


def list_rounds(rdir: Path) -> list[Path]:
    return sorted(rounds_dir(rdir).glob("round-*.json"))


def load(f: Path) -> dict:
    return json.loads(f.read_text(encoding="utf-8"))


def save(f: Path, data: dict) -> None:
    f.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(data: dict) -> None:
    qs = data.get("questions")
    if not isinstance(qs, list) or not qs:
        raise SystemExit("round needs a non-empty 'questions' list")
    for i, q in enumerate(qs, 1):
        q.setdefault("id", f"q{i}")
        q.setdefault("type", "choice" if q.get("options") else "open")
        if not q.get("text"):
            raise SystemExit(f"question {q['id']} has no 'text'")
        if q["type"] == "choice" and not q.get("options"):
            raise SystemExit(f"question {q['id']} is 'choice' but has no options")


def new_round(rdir: Path, data: dict) -> Path:
    validate(data)
    rounds_dir(rdir).mkdir(exist_ok=True)
    n = len(list_rounds(rdir)) + 1
    data.update({"round": n, "status": "open", "answers": {}, "created_at": dt.datetime.now().isoformat("T", "seconds")})
    f = rounds_dir(rdir) / f"round-{n:02d}.json"
    save(f, data)
    return f


def open_round(rdir: Path) -> Path | None:
    for f in reversed(list_rounds(rdir)):
        if load(f).get("status") == "open":
            return f
    return None


def answer_round(f: Path, answers: dict, via: str) -> dict:
    data = load(f)
    data["answers"] = answers
    data["status"] = "answered"
    data["answered_at"] = dt.datetime.now().isoformat("T", "seconds")
    data["answered_via"] = via
    save(f, data)
    return data


def format_answers(data: dict) -> str:
    """Plain text the agent can read back: one line per question."""
    out = [f"Round {data.get('round')} — {data.get('title', '')} (answered via {data.get('answered_via')})"]
    for q in data["questions"]:
        a = data.get("answers", {}).get(q["id"], {})
        if q["type"] == "choice":
            label = next((o["label"] for o in q["options"] if o["key"] == a.get("choice")), a.get("choice", "—"))
            line = f"- {q['id']}: {q['text']} → {a.get('choice', '—')}) {label}"
        else:
            line = f"- {q['id']}: {q['text']} → {a.get('text', '—')}"
        if a.get("note"):
            line += f"  [note: {a['note']}]"
        out.append(line)
    return "\n".join(out)


def wait_round(f: Path, timeout: int) -> dict | None:
    end = time.time() + timeout
    while time.time() < end:
        data = load(f)
        if data.get("status") == "answered":
            return data
        time.sleep(3)
    return None


# ---------------------------------------------------------------- plan review

def plan_review(rdir: Path) -> Path:
    plan = rdir / "PLAN.md"
    if not plan.exists():
        raise SystemExit(f"No PLAN.md in {rdir}")
    set_front(plan, "status", "review")
    return plan


def plan_decide(rdir: Path, approve: bool, comments: str, via: str) -> str:
    plan = rdir / "PLAN.md"
    if approve:  # an invalid or PLAN.md-contradicting PLAN.json (opt-in contract) is never approved
        import bt_plan_adapter
        import bt_scheduler_adapter
        compatibility_report = bt_scheduler_adapter.plan_compatibility_report(rdir)
        problem = bt_plan_adapter.publishable_problem(rdir, compatibility_report=compatibility_report)
        if problem:
            raise SystemExit(problem)
    stamp = f"{dt.datetime.now():%Y-%m-%d %H:%M}"
    with plan.open("a", encoding="utf-8") as fh:
        if comments.strip():
            fh.write(f"- {stamp} review comments ({via}): {comments.strip()}\n")
        fh.write(f"- {stamp} plan {'APPROVED' if approve else 'CHANGES REQUESTED'} ({via})\n")
    status = "approved" if approve else "changes-requested"
    set_front(plan, "status", status)
    if approve:  # freeze exactly what was just approved: later launches are compared against this revision
        import bt_plan_adapter
        import bt_scheduler_adapter
        bt_plan_adapter.freeze_approved(
            rdir, compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir)
        )
    return status


def wait_plan(rdir: Path, timeout: int) -> str | None:
    plan = rdir / "PLAN.md"
    end = time.time() + timeout
    while time.time() < end:
        status = _front(plan, "status")
        if status != "review":
            return status
        time.sleep(3)
    return None
