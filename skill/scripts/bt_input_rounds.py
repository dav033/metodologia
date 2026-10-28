"""A question for every Planner assumption that waits for the owner, opened by the system and applied by the system.

A SPEC `## Inputs` row whose `where` says it is a Planner assumption and whose status is still `pending` blocks the
subplan it names («faltan entradas»), yet nothing made the Planner ask: REQ-021's SP-3 sat there with no question and no
button, and the confirm button stayed off. `ensure` opens ONE round with a confirm-or-change question per such row of the
focused subplan; `apply_answers` writes the owner's answer back (a confirmation marks the row resolved in SPEC.md, a change
becomes a note for the Planner) so the flow moves even when the Planner is not running.

Only rows that are assumptions are asked: a key, a path or a password the owner must supply is never turned into yes/no.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import bt_rounds as rounds

_ASSUMPTION = re.compile(r"assum|suposic|supuesto", re.IGNORECASE)
_OWNER = re.compile(r"owner|propietari|dueñ", re.IGNORECASE)


def _key(item: str) -> str:
    return hashlib.sha256(" ".join(item.split()).encode("utf-8")).hexdigest()[:12]


def assumptions(rdir: Path, subplan: str) -> list[dict]:
    """Pending owner-owned Planner assumptions that name this subplan."""
    import bt_planning_flow as flow

    return [row for row in flow.inputs_for(rdir, subplan)
            if row["subplans"] and row["pending"] and _ASSUMPTION.search(row["where"]) and _OWNER.search(row["who"])]


def _covered(rdir: Path) -> set[str]:
    done: set[str] = set()
    for f in rounds.list_rounds(rdir):
        try:
            done |= {entry.get("key", "") for entry in rounds.load(f).get("auto_input") or [] if isinstance(entry, dict)}
        except (OSError, ValueError):
            continue
    return done


def ensure(rdir: Path, state: dict | None = None) -> Path | None:
    """Open the confirmation round for the focused subplan when it has unasked assumptions and no round is open.
    Idempotent: an item already asked (open or answered) is never asked again. Returns the new round file or None."""
    import bt_planning_flow as flow

    try:
        if not flow.active(rdir):
            return None
        state = state if state is not None else flow.state(rdir)
        focus = state.get("focus") or ""
        if not focus or state.get("editing") or rounds.open_round(rdir) is not None:
            return None
        asked = _covered(rdir)
        rows = [r for r in assumptions(rdir, focus) if _key(r["item"]) not in asked]
        if not rows:
            return None
        questions, auto = [], []
        for number, row in enumerate(rows, 1):
            questions.append({
                "id": f"q{number}", "type": "choice", "recommended": "a",
                "text": f"El Planner supone esto para {focus}: «{row['item']}». ¿Lo confirmas?",
                "options": [{"key": "a", "label": "Sí, lo confirmo tal como está"},
                            {"key": "b", "label": "No, quiero cambiarlo (explícalo en el comentario)"}],
                "why": f"Es una suposición del Planner ({row['where']}), no una decisión tuya. Mientras siga pendiente, "
                       f"{focus} no se puede confirmar.",
            })
            auto.append({"id": f"q{number}", "key": _key(row["item"]), "item": row["item"]})
        return rounds.new_round(rdir, {
            "title": f"{focus} — Confirmar suposiciones del Planner", "coverage": focus,
            "intro": f"Para confirmar {focus} faltan {len(rows)} suposición(es) del Planner que solo tú puedes confirmar o cambiar.",
            "questions": questions, "auto_input": auto})
    except (OSError, ValueError, SystemExit):
        return None


def _mark_resolved(rdir: Path, item: str, note: str) -> bool:
    """Set the Status cell of the SPEC Inputs row for `item` to `resolved: …`."""
    path = Path(rdir) / "SPEC.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeError):
        return False
    header: list[str] | None = None
    wanted = " ".join(item.split())
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        labels = [c.lower().strip("*` ") for c in cells]
        if header is None:
            header = labels
            continue
        item_col = next((i for i, c in enumerate(header) if c.startswith(("item", "input"))), None)
        status_col = next((i for i, c in enumerate(header) if c.startswith(("status", "estado"))), None)
        if item_col is None or status_col is None or len(cells) <= max(item_col, status_col):
            continue
        if " ".join(cells[item_col].replace("\\|", "|").split()) == wanted:
            cells[status_col] = f"resolved: {note}"
            lines[index] = "| " + " | ".join(cells) + " |" + ("\n" if line.endswith("\n") else "")
            path.write_text("".join(lines), encoding="utf-8")
            return True
    return False


def apply_answers(rdir: Path, data: dict) -> list[str]:
    """After the owner answers a round `ensure` opened: confirm → the SPEC row is resolved; change → a note for the Planner.
    Returns what was done, one line per question; a round that is not an auto round returns []."""
    auto = {entry["id"]: entry for entry in data.get("auto_input") or [] if isinstance(entry, dict) and entry.get("id")}
    done: list[str] = []
    for qid, entry in auto.items():
        answer = (data.get("answers") or {}).get(qid) or {}
        choice, note = answer.get("choice"), (answer.get("note") or "").strip()
        if choice == "a":
            ok = _mark_resolved(rdir, entry["item"], f"owner confirmed in round {data.get('round')}")
            done.append(f"{qid}: confirmed" + ("" if ok else " (the SPEC row was not found: the Planner must mark it)"))
        elif choice == "b":
            import bt_planning_notes as notes
            notes.add(rdir, f"Owner does NOT confirm the assumption «{entry['item']}» (round {data.get('round')}). "
                            f"What to change: {note or 'not said'}. Update SPEC/PLAN and ask again if needed.",
                      kind="decision", by="owner")
            done.append(f"{qid}: owner wants a change")
    return done
