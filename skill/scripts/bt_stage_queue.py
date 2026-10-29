"""Stages that wait for earlier subplans (pictures REQ-021, 2026-10-29: «Ejecutar SP-8» while SP-7 was still being
designed was refused with plan errors about SP-7's tasks and gates).

When «Ejecutar SP-N» fails only because the stage needs subplans that have not run yet, it is queued in
`.planning/stage-queue.json` instead of refused: it runs by itself when the owner approves, in «Probar», every subplan it
waits for (`drain`, called from `bt_verification.decide`). Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import bt_planning_activity as activity

FILE = ".planning/stage-queue.json"


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def pending(rdir: Path) -> list[dict]:
    try:
        items = json.loads((Path(rdir) / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return []
    return [i for i in items if isinstance(i, dict) and i.get("add") and i.get("after")] if isinstance(items, list) else []


def _save(rdir: Path, items: list[dict]) -> None:
    target = Path(rdir) / FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)


def needs(rdir: Path, add: list[str], report: dict | None = None) -> list[str]:
    """The subplans not run yet that the stage of `add` needs: the shortest run of subplans just before it (plan order,
    outside the approved stage) with which its gate passes; [] when none makes it pass."""
    import bt_plan_adapter
    import bt_scheduler_adapter
    from bt_stages import approved

    order = bt_plan_adapter.draft_subplans(rdir) or []
    if not add or add[0] not in order:
        return []
    held = set(approved(rdir))
    before = [s for s in order[:order.index(add[0])] if s not in held]
    report = report if report is not None else bt_scheduler_adapter.plan_compatibility_report(rdir)
    for size in range(1, len(before) + 1):
        if bt_plan_adapter.stage_problem(rdir, [*before[-size:], *add], compatibility_report=report) is None:
            return before[-size:]
    return []


def queue(rdir: Path, add: list[str], after: list[str], *, by: str, via: str) -> str:
    items = [i for i in pending(rdir) if i["add"] != add]
    items.append({"add": add, "after": after, "by": by, "via": via, "at": _now()})
    _save(rdir, items)
    names, waits = ", ".join(add), ", ".join(after)
    activity.record(rdir, "Tú" if by == "owner" else by, f"Ejecutar {names}: en cola hasta que {waits} se ejecute y lo "
                    "apruebes en «Probar»", kind="flow", sp=add[0])
    return (f"{names} depende de {waits}, que todavía no se ha ejecutado. Quedó en cola: se ejecutará solo cuando {waits} "
            f"se haya ejecutado y lo apruebes en «Probar».")


def settle(rdir: Path, held: list[str]) -> None:
    """Drop the queued stages whose subplans all run already in the approved stage (pictures REQ-021, 2026-10-29: SP-8
    queued behind SP-7, then the owner ran SP-7 and SP-8 from their buttons; the stale entry would have approved a second,
    identical stage when SP-7 passed «Probar»)."""
    items = pending(rdir)
    left = [i for i in items if not set(i["add"]) <= set(held)]
    if len(left) != len(items):
        _save(rdir, left)


def drain(project: str, rdir: Path) -> list[str]:
    """Run every queued stage whose subplans to wait for are all approved in «Probar». Returns what each one said; a
    stage that still cannot run stays queued with its error, which the activity feed shows."""
    import bt_stages
    import bt_verification

    settle(rdir, bt_stages.approved(rdir))
    items = pending(rdir)
    if not items:
        return []
    approved = {r["id"] for r in bt_verification.state(rdir)["subplans"] if r["state"] == "approved"}
    said, left = [], []
    for item in items:
        if not set(item["after"]) <= approved:
            left.append(item)
            continue
        try:
            said.append(bt_stages.run(project, rdir, item["add"], by=item.get("by", "owner"), via="stage-queue"))
        except bt_stages.StageError as exc:
            left.append({**item, "error": f"{exc.message} [{exc.code}]"[:400], "tried": _now()})
            activity.record(rdir, "Plan", f"No se pudo ejecutar {', '.join(item['add'])} de la cola: {exc.message}"[:300],
                            kind="flow", sp=item["add"][0])
    _save(rdir, left)
    return said
