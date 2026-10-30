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


_SIGN_IN = re.compile(r"\s*\b(?:e\s+|y\s+)?inici(?:a|e|ar)\s+sesi[oó]n\s+como\s+([\w.+-]+@[\w-]+(?:\.[\w-]+)+)",
                      re.IGNORECASE)
_ROLE_ALIAS = {"admin": "administrador", "designer-plus": "designer_plus", "master-designer": "master_designer",
               "empleado": "empleado_interno", "master": "master_designer"}


def test_account(email: str, accounts: list[str]) -> str:
    """The recipe's test account for an account the plan names (admin@prueba.local → test+administrador@…): the plan was
    written before the seeded accounts existed (owner, 2026-10-30: the guide asked for admin@prueba.local, which the test
    database does not have, D-211). The plan's own address when nothing matches."""
    local = email.split("@", 1)[0].lower().removeprefix("test+")
    role = _ROLE_ALIAS.get(local, local.replace("-", "_"))
    return next((a for a in accounts if a.split("@", 1)[0].lower() == f"test+{role}"), email)


def signed_in(text: str, accounts: list[str]) -> str:
    """A step that asks to sign in, when «Probar» already opens the version signed in (D-205): it says so, naming the
    account to pick in «Entras como» when the step needs a given one."""
    def say(m: re.Match) -> str:
        return f" (ya entras con sesión iniciada; en «Entras como» elige {test_account(m.group(1), accounts)})"
    return _SIGN_IN.sub(say, text)


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
    login = (recipe or {}).get("auto_login") if isinstance((recipe or {}).get("auto_login"), dict) else {}
    signed = ""
    if login:                                          # D-211: the session is already open; no password to look for
        tests = [str(a) for a in login.get("accounts") or [] if isinstance(a, str)]
        steps = [{"do": signed_in(s["do"], tests), "expect": signed_in(s["expect"], tests)} for s in steps]
        before = [signed_in(b, tests) for b in before if not _SEED.search(b)]
        signed = str(login.get("default") or (tests[0] if tests else ""))
        accounts, password = [test_account(a, tests) for a in accounts], ""
    return {"steps": steps[:MAX_STEPS], "more": more, "before": before, "expect": expect_all, "done": done, "accounts": accounts, "password": password,
            "signed": signed,
            "commands": commands, "dev": bool(_DEV.search(text_all)), "design": _design(root, project, rdir, sid),
            "source": source}


# ------------------------------------------------------------------ a task's manual check («Probar esto»)

_WORD = re.compile(r"[a-záéíóúñ]{4,}")
_STOP = frozenset("that this with from into then them they their there when which while only also each every never "
                  "without record exact text free secrets separate already using receives".split())
_PAIR = re.compile(r"\benglish\b.*\bspanish\b|\bspanish\b.*\benglish\b|\binglés\b.*\bespañol\b|\bespañol\b.*\binglés\b",
                   re.I | re.S)
_CHAT = re.compile(r"\b(chat|conversation|conversación|reply|respuesta|assistant|asistente)\b", re.I)
_PROVIDER = re.compile(r"(PROVEEDOR|PROVIDER|CHAT_MODEL)$")
_PLAIN = re.compile(r"[\w.:/-]{1,60}")
# what a language-pair check asks the owner to type: one request per language, same meaning, no answer to copy
SAY = {"en": "Hi! I'm planning a birthday party. Which balloon decoration would you suggest, and in which colours?",
       "es": "¡Hola! Estoy organizando un cumpleaños. ¿Qué decoración con globos me sugieres y en qué colores?"}


def manual_checks(rdir: Path, task: str) -> list[dict]:
    for item in _plan(rdir).get("tasks") or []:
        if isinstance(item, dict) and item.get("id") == task:
            return [{"value": str(v.get("value") or ""), "purpose": str(v.get("purpose") or ""),
                     "expected": str(v.get("expected") or v.get("purpose") or "")}
                    for v in item.get("verification") or [] if isinstance(v, dict) and v.get("type") == "manual"]
    return []


def _subplan_of(rdir: Path, task: str) -> str:
    item = next((t for t in _plan(rdir).get("tasks") or [] if isinstance(t, dict) and t.get("id") == task), {})
    return str(item.get("subplan_id") or item.get("subplan") or "")


def _related(rdir: Path, sid: str, text: str, limit: int = 2) -> list[str]:
    """The sentences of the subplan's `## Pruebas` How cell that share most words with the check (the Spanish sentence at
    the same place when both renderings split alike)."""
    english = [r for r in verification.tests(rdir) if sid in r["subplans"]]
    spanish = [r for r in verification.tests(rdir, "SPEC.es.md") if sid in r["subplans"]]
    if not english:
        return []
    en, es = sentences(english[0]["how"]), sentences(spanish[0]["how"]) if spanish else []
    want = {w for w in _WORD.findall(text.lower()) if w not in _STOP}
    scored = sorted(((len(want & set(_WORD.findall(s.lower()))), i) for i, s in enumerate(en) if "`" not in s),
                    key=lambda x: (-x[0], x[1]))                       # a command is not something the owner observes
    chosen = sorted(i for score, i in scored[:limit] if score >= 2)
    return [(es[i] if len(es) == len(en) else en[i]) for i in chosen]


def provider(recipe: dict | None) -> str:
    """The configured AI provider and model named in the recipe's env file (names such as IA_PROVEEDOR or
    GEMINI_CHAT_MODEL; a value that is not a short plain word is never shown)."""
    if not recipe or not recipe.get("env_file"):
        return ""
    import bt_verifier_env
    import os
    env = dict(bt_verifier_env.load(os.path.expanduser(str(recipe["env_file"])))[0])
    found = [f"{k}={v}" for k, v in sorted(env.items()) if _PROVIDER.search(k) and _PLAIN.fullmatch(v or "")]
    return ", ".join(found)


def manual(root: Path, project: str, rdir: Path, task: str, *, url: str = "", recipe: dict | None = None,
           attempt: str = "", commit: str = "") -> dict:
    """«Probar esto» for a task whose decision waits for manual evidence: {steps: [{do, expect}], checks, accounts,
    password, provider, prefill}. Deterministic: the task's manual checks, the related sentences of its subplan's
    `## Pruebas` row, and for a check that compares English with Spanish one message to type in each language."""
    checks = manual_checks(rdir, task)
    text = " ".join(f"{c['value']} {c['purpose']}" for c in checks)
    sid = _subplan_of(rdir, task)
    origin = (re.match(r"https?://[^/]+", url or "") or [""])[0]
    own = " ".join(f"{r.get('how') or ''}" for r in _rows(rdir, sid)[0]) if sid else ""
    every = " ".join(f"{r.get('how') or ''} {r.get('expect') or ''}" for r in verification.tests(rdir))
    roles = re.findall(r"\b(Designer Plus|Master Designer|Entusiasta|Designer|Empleado|Admin\w*)\b", own + " " + text)
    accounts = []
    for role in dict.fromkeys(roles):
        wanted = re.sub(r"[^a-z]+", "-", role.lower()).strip("-").replace("administrador", "admin").replace("administrator", "admin")
        accounts += [m for m in dict.fromkeys(m.group(0).rstrip(".") for m in _EMAIL.finditer(every))
                     if m.split("@")[0] == wanted and m not in accounts]
    login = (recipe or {}).get("auto_login") if isinstance((recipe or {}).get("auto_login"), dict) else {}
    tests = [str(a) for a in (login or {}).get("accounts") or [] if isinstance(a, str)]
    if login:                                          # D-211: the link opens it signed in as the account the check needs
        accounts = [test_account(a, tests) for a in accounts] or [str(login.get("default") or "")]
        steps = [{"do": f"Abre {origin + '/' if origin else 'la dirección de prueba'} con el enlace de arriba: entras ya "
                        f"con sesión iniciada; en «Entras como» elige {accounts[0]}.", "expect": ""}]
    else:
        steps = [{"do": f"Abre {origin + '/' if origin else 'la dirección de prueba'}" +
                        (f" e inicia sesión como {accounts[0]}." if accounts else "."), "expect": ""}]
    steps += [{"do": _with_origin(s, origin), "expect": ""} for s in _related(rdir, sid, text, 1)] if sid else []
    pair = bool(_PAIR.search(text))
    if pair:
        where = "el chat" if _CHAT.search(text) else "la pantalla que nombra la comprobación"
        steps += [{"do": f"Cambia el idioma a inglés (selector EN) y en {where} escribe: «{SAY['en']}»",
                   "expect": "La respuesta llega en inglés."},
                  {"do": f"Cambia el idioma a español (selector ES), abre una conversación nueva y escribe: «{SAY['es']}»",
                   "expect": "La respuesta llega en español."}]
    for check in checks:
        steps.append({"do": "Comprueba lo que pide el plan: " + check["value"], "expect": check["expected"]})
    seed = _SEED.search(every)
    note = (recipe or {}).get("accounts")
    password = ("" if login else note.strip() if isinstance(note, str) and note.strip() else
                f"la contraseña es la que escribiste al ejecutar `{seed.group(1)}`; la bitácora no la guarda." if accounts and seed
                else "")
    named = provider(recipe)
    prefill = (f"Probé {task} en local (intento {attempt or '?'}, commit {commit[:10] or '?'}) con el proveedor configurado"
               f"{' (' + named + ')' if named else ''}" +
               (": una conversación en inglés recibió respuesta en inglés y una en español, respuesta en español." if pair
                else ": " + "; ".join(c["value"] for c in checks) + " — funciona como se espera."))
    return {"steps": steps[:MAX_STEPS], "checks": checks, "accounts": accounts, "password": password,
            "provider": named, "prefill": prefill, "pair": pair}
