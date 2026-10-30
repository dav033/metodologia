"""«Cómo probar esta versión»: 3–8 concrete steps for a subplan version, next to its URL in «Probar».

Owner, 2026-10-30: «una descripción corta de cómo y qué exactamente probar». Built deterministically from what the plan
already says, in this order:

1. the subplan's row in SPEC `## Pruebas` (SPEC.es.md when it has one, so the owner reads Spanish): its How and Expect
   cells, split on their numbered items «1) … 2) …» and paired by number, so every step says what to do and what to see;
   a row that starts «With SP-N's setup» / «Con la configuración de SP-N» brings that subplan's first step as a
   one-time preparation;
2. without such a row, the `verification` entries of the subplan's tasks that a person runs (`manual`, `browser`);
3. else its acceptance criteria, each as «Comprueba: …».

Local URLs in the text (`http://localhost:3000/…`) become the version's own URL. Accounts are the e-mail addresses the
steps name; a password is never shown: the recipe's `accounts` text says where it comes from, else the seed command the
steps name. A UI subplan links its approved design contract. Pure functions; standard library only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import bt_verification as verification

MAX_STEPS = 8
_NUMBERED = re.compile(r"(?:(?<=\s)|^)(\d{1,2})\)\s+")
_LOCAL_URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1)(?::\d{1,5})?")
_EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9][\w.+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_SETUP = re.compile(r"^\s*(?:With|Con la configuración de|Con el entorno de)\s+(SP-\d+)(?:'s setup)?\s*[:,.]\s*", re.I)
_SEED = re.compile(r"`([^`]*(?:sembrar|seed)[^`]*)`", re.I)
_COMMAND = re.compile(r"`((?:npm|npx|uv|python3?|node)\s[^`]+)`")
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«])")
_DEV = re.compile(r"`npm run dev`|`next dev`")


def numbered(text: str) -> tuple[str, dict[int, str]]:
    """(text before the first «N)», {N: item}) of a table cell. Items count up from 1, so a «2)» inside an item («repeat
    step 2)») stays part of it."""
    text = " ".join((text or "").split())
    marks, expected = [], 1
    for found in _NUMBERED.finditer(text):
        if int(found.group(1)) == expected:
            marks.append(found)
            expected += 1
    if not marks:
        return text, {}
    items: dict[int, str] = {}
    for i, found in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        items[int(found.group(1))] = text[found.end():end].strip().rstrip(";").strip()
    return text[:marks[0].start()].strip(), items


def sentences(text: str) -> list[str]:
    """A paragraph cell as its sentences (a row written without «1) 2)» still becomes steps)."""
    return [p.strip() for p in _SENTENCE.split(" ".join((text or "").split())) if p.strip()]


def _rows(rdir: Path, sid: str) -> tuple[list[dict], str]:
    """(the subplan's own `## Pruebas` rows, the file they come from): Spanish when SPEC.es.md has as many rows for it
    as SPEC.md, each keeping the English row's kind (the Spanish Where cell does not start with «Local»)."""
    english = [r for r in verification.tests(rdir) if sid in r["subplans"]]
    spanish = [r for r in verification.tests(rdir, "SPEC.es.md") if sid in r["subplans"]]
    if english and all(r["kind"] == "none" for r in english):          # nothing to try by hand: its How is the reason
        return [], ""
    if spanish and len(spanish) == len(english):
        return [{**es, "kind": en["kind"]} for es, en in zip(spanish, english)], "SPEC.es.md"
    return (english, "SPEC.md") if english else (spanish, "SPEC.es.md" if spanish else "")


def _with_origin(text: str, origin: str) -> str:
    return _LOCAL_URL.sub(origin, text) if origin else text


def _plan(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _from_plan(rdir: Path, sid: str) -> list[dict]:
    plan = _plan(rdir)
    steps = []
    for task in plan.get("tasks") or []:
        if not isinstance(task, dict) or (task.get("subplan_id") or task.get("subplan")) != sid:
            continue
        for check in task.get("verification") or []:
            if isinstance(check, dict) and check.get("type") in ("manual", "browser") and check.get("value"):
                steps.append({"do": str(check["value"]), "expect": str(check.get("purpose") or "")})
    if steps:
        return steps
    sub = next((s for s in plan.get("subplans") or [] if isinstance(s, dict) and s.get("id") == sid), {})
    return [{"do": "Comprueba: " + str(c), "expect": ""} for c in sub.get("acceptance_criteria") or [] if str(c).strip()]


def _design(root: Path, project: str, rdir: Path, sid: str) -> dict | None:
    sub = next((s for s in _plan(rdir).get("subplans") or [] if isinstance(s, dict) and s.get("id") == sid), {})
    ui = sub.get("ui") if isinstance(sub.get("ui"), dict) else None
    if not ui or not ui.get("contract"):
        return None
    ref = f"{ui['contract']}@v{ui.get('version') or 1}"
    for name in (f"design/contracts/{ref}.es.md", f"design/{ref}.es.md", f"design/contracts/{ref}.md", f"design/{ref}.md"):
        if (Path(rdir) / name).is_file():
            try:
                rel = (Path(rdir) / name).resolve().relative_to((Path(root) / project).resolve())
            except ValueError:
                rel = None
            return {"ref": ref, "doc": str(rel) if rel else ""}
    return {"ref": ref, "doc": ""}


def guide(root: Path, project: str, rdir: Path, sid: str, *, url: str = "", recipe: dict | None = None,
          copy: Path | None = None) -> dict:
    """{steps: [{do, expect}] (at most MAX_STEPS; `more` says how many were left out), expect: what to see overall,
    before: one-time preparation, done: preparation «Probar» already runs, accounts, password (where it comes from,
    never its value), commands (how to open a terminal with the version's environment), dev, design, source}."""
    origin = (re.match(r"https?://[^/]+", url or "") or [""])[0]
    rows, source = _rows(rdir, sid)
    steps: list[dict] = []
    before: list[str] = []
    text_all = ""
    expect_all: list[str] = []
    own_text = ""
    for row in rows:
        how = row.get("how") or ""
        setup = _SETUP.match(how)
        if setup:
            how = how[setup.end():]
            first = _rows(rdir, setup.group(1))[0]
            if first:
                lead, items = numbered(first[0].get("how") or "")
                prep = items.get(min(items)) if items else lead
                if prep:
                    before.append(f"Una sola vez, de {setup.group(1)}: {_with_origin(prep, origin)}")
                    text_all += " " + prep
        lead, todo = numbered(how)
        general, seen = numbered(row.get("expect") or "")
        own_text += f" {row.get('how') or ''} {row.get('expect') or ''}"
        if lead and todo:
            before.append(_with_origin(lead, origin))
        if todo:
            for n in sorted(todo):
                steps.append({"do": _with_origin(todo[n], origin), "expect": _with_origin(seen.get(n, ""), origin)})
            if general:
                expect_all.append(_with_origin(general, origin))
        else:
            steps += [{"do": _with_origin(part, origin), "expect": ""} for part in sentences(how)]
            expect_all += [_with_origin(part, origin) for part in sentences(general)]
    text_all += own_text
    if not steps:
        steps = [{"do": _with_origin(s["do"], origin), "expect": _with_origin(s["expect"], origin)} for s in _from_plan(rdir, sid)]
        source = "PLAN.json" if steps else ""
        own_text = " ".join(s["do"] + " " + s["expect"] for s in steps)
        text_all += own_text
    more = max(0, len(steps) - MAX_STEPS)
    accounts = list(dict.fromkeys(m.group(0).rstrip(".") for m in _EMAIL.finditer(own_text)))
    seed = _SEED.search(text_all)
    note = (recipe or {}).get("accounts")
    if isinstance(note, list):
        note = " ".join(str(n) for n in note)
    if isinstance(note, str) and note.strip():
        password = note.strip()
    elif accounts and seed:
        password = f"la contraseña es la que escribiste al ejecutar `{seed.group(1)}`; la bitácora no la guarda."
    elif accounts:
        password = "la contraseña no está en la bitácora: es la que se definió al crear esas cuentas."
    else:
        password = ""
    commands = ""
    needs = [c for c in _COMMAND.findall(text_all) if not _DEV.search(f"`{c}`")]
    if needs and copy is not None:
        env = f"{copy}.env"
        commands = f"cd {copy} && set -a && . {env} && set +a"
    done = [f"«Probar» ya ejecuta `{step['run']}` al arrancar." for step in (recipe or {}).get("prepare") or []
            if isinstance(step, dict) and isinstance(step.get("run"), str) and f"`{step['run']}`" in text_all]
    return {"steps": steps[:MAX_STEPS], "more": more, "before": before, "expect": expect_all, "done": done, "accounts": accounts, "password": password,
            "commands": commands, "dev": bool(_DEV.search(text_all)), "design": _design(root, project, rdir, sid),
            "source": source}
