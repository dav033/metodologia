"""CLI side of the question-round and plan-review flows (the web UI is the other side)."""
from __future__ import annotations

import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_vcs import commit


def _web(project: str, rid: str, tab: str) -> str:
    from bt_server import ensure_server
    return f"{ensure_server()}/p/{project}/req/{rid}?tab={tab}"


def run_flow(a, project: str, pdir: Path) -> None:
    rdir = find_req(pdir, a.req)
    rid = req_id(rdir)
    if a.cmd == "round":
        return _round(a, project, rdir, rid)
    return _plan(a, project, rdir, rid)


def _round(a, project: str, rdir: Path, rid: str) -> None:
    if a.action == "new":
        if not a.file:
            raise SystemExit("round new needs --file <round.json>")
        f = rounds.new_round(rdir, json.loads(Path(a.file).read_text(encoding="utf-8")))
        commit(ROOT, f"{project}: {rid} {f.stem} posted")
        print(json.dumps({"round_file": f.as_posix(), "url": _web(project, rid, "rounds")}, indent=1))
        return
    f = rounds.open_round(rdir)
    if a.action == "show":
        last = f or (rounds.list_rounds(rdir) or [None])[-1]
        if not last:
            raise SystemExit("no rounds yet")
        data = rounds.load(last)
        print(rounds.format_answers(data) if data.get("status") == "answered" else json.dumps(data, indent=1,
                                                                                              ensure_ascii=False))
        return
    if not f:
        raise SystemExit("no open round")
    if a.action == "answer":
        if not a.file:
            raise SystemExit("round answer needs --file <answers.json>  ({\"q1\": {\"choice\": \"a\"}, ...})")
        data = rounds.answer_round(f, json.loads(Path(a.file).read_text(encoding="utf-8")), "terminal")
        import bt_input_rounds
        applied = bt_input_rounds.apply_answers(rdir, data)
        commit(ROOT, f"{project}: {rid} answers to {f.stem} (terminal)")
        print(rounds.format_answers(data))
        for line in applied:
            print(f"applied: {line}")
        return
    data = rounds.wait_round(f, a.timeout)  # wait
    print(rounds.format_answers(data) if data else f"timeout: {f.name} still open")


def _plan(a, project: str, rdir: Path, rid: str) -> None:
    if a.action == "review":
        rounds.plan_review(rdir)
        commit(ROOT, f"{project}: {rid} plan ready for review")
        print(json.dumps({"plan": (rdir / "PLAN.md").as_posix(), "url": _web(project, rid, "plan")}, indent=1))
    elif a.action in ("approve", "changes"):
        status = rounds.plan_decide(rdir, a.action == "approve", a.comments, "terminal")
        commit(ROOT, f"{project}: {rid} plan {status} (terminal)")
        print(status)
    else:  # wait
        status = rounds.wait_plan(rdir, a.timeout)
        print(status or "timeout: plan still in review")
