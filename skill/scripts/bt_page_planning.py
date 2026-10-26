"""Plan tab of a requirement while it is being planned (layout approved on the "Planificación" design canvas).

Three modes share one top bar (mode, language EN/ES/EN+ES, translation and design status, approval dialog):
- `subplans` (default): subplan list by milestone · the selected subplan (Diseño / Tareas / Criterios) · what changed
  in the conversation;
- `review`: one subplan's design at a chosen width and draft revision, with its contract, criteria and comments;
- `doc`: the whole PLAN.md, original and translation side by side, changed sections first with their diff.

The tab is a live region: `planning-live.js` polls `fragment()` and swaps only the blocks (`data-k`) whose digest
changed, so the conversation's edits, the Designer's drafts and the translation appear without a reload.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
import threading
import time
from html import escape as e
from pathlib import Path
from urllib.parse import urlencode

import bt_design_drafts as drafts
import bt_planning_activity as activity
import bt_translate as tr
from bt_core import _front
from bt_pages import purl

LANGS = (("en", "EN"), ("es", "ES"), ("both", "EN + ES"))
MODES = (("subplans", "Subplanes"), ("doc", "Plan completo"))
VIEWS = ("design", "tasks", "criteria")
STATES = {"none": "sin diseño", "queued": "diseño en cola", "drafting": "diseñando…", "ready": "diseño listo",
          "failed": "error de diseño", "approved": "aprobado con el plan"}
REASONS = {"requested": "pedido desde la conversación", "web": "pedido desde la web",
           "feedback": "aplicando tus comentarios", "plan changed": "el subplan cambió"}
SEND = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'aria-hidden="true"><path d="M4 12l16-8-6 16-2-7-8-1z"/></svg>')
_FOLLOW_SEC = 10
_followed: dict[str, float] = {}
_follow_lock = threading.Lock()


def default_lang(rdir: Path) -> str:
    return "es" if (Path(rdir) / "PLAN.es.md").is_file() else "en"


def options(rdir: Path, q: dict) -> dict:
    """Validated view options from the query string."""
    sp = q.get("sp", "")
    return {"lang": q.get("lang") if q.get("lang") in dict(LANGS) else default_lang(rdir),
            "mode": q.get("mode") if q.get("mode") in ("subplans", "doc", "review") else "subplans",
            "view": q.get("view") if q.get("view") in VIEWS else "design",
            "sp": sp if re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", sp) else "",
            "rev": int(q["rev"]) if _number(q.get("rev", "")) else 0,
            "only": q.get("only") == "1",
            "filter": q.get("filter") if q.get("filter") in ("ui", "changed") else ""}


def _number(value: object) -> bool:
    return isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 6


def link(project: str, rid: str, opts: dict, **change) -> str:
    """Page URL of the Plan tab with `opts` changed; JS turns it into the fragment URL for live navigation."""
    merged = {**opts, **change}
    query = {"tab": "plan", "lang": merged["lang"], "mode": merged["mode"], "view": merged["view"],
             "sp": merged["sp"], "rev": merged["rev"] or "", "only": "1" if merged["only"] else "",
             "filter": merged.get("filter") or ""}
    return purl(project, "req", rid) + "?" + urlencode({k: v for k, v in query.items() if v != ""})


def follow(project: str, rdir: Path, lang: str = "en") -> None:
    """Let the Designer and the translator catch up with the conversation, at most every few seconds per requirement.
    Only requirements with planning-time design, or a Spanish view being read, start any background work."""
    if not drafts.active(rdir) and lang == "en":
        return
    key = str(rdir)
    with _follow_lock:
        if time.time() - _followed.get(key, 0) < _FOLLOW_SEC:
            return
        _followed[key] = time.time()

    def run():
        try:
            drafts.sync(project, rdir)
            tr.ensure(project, rdir)
        except (SystemExit, Exception):  # noqa: BLE001, S110 - a page poll never fails on background work
            pass
    threading.Thread(target=run, daemon=True).start()


def plan_tab(project: str, rid: str, rdir: Path, status: str | None, token: str, q: dict) -> str:
    opts = options(rdir, q)
    api = purl(project, "req", rid, "planning")
    return (f'<div class="pp" id="planning" data-api="{e(api)}">{fragment(project, rid, rdir, status, token, opts)}'
            '</div><script src="/static/planning-live.js"></script>')


def fragment(project: str, rid: str, rdir: Path, status: str | None, token: str, opts: dict) -> str:
    import bt_page_planning_views as views
    activity.observe(rdir)
    ctx = {"project": project, "rid": rid, "rdir": Path(rdir), "status": status, "token": token, "opts": opts,
           "cache": tr.load_cache(rdir) if opts["lang"] != "en" else {}, "subplans": drafts.subplans(rdir),
           "rows": {row["ref"]: row for row in drafts.rows(rdir)}}
    if not opts["sp"] or opts["sp"] not in {s["id"] for s in ctx["subplans"]}:
        opts["sp"] = _default_subplan(rdir, ctx["subplans"])
    if opts["mode"] == "doc" or not ctx["subplans"]:
        body = [views.document(ctx)]
    elif opts["mode"] == "review":
        body = [views.review(ctx)]
    else:
        body = ['<div class="pp-grid">', _stamp(_list(ctx)), _stamp(_detail(ctx)), _stamp(_feed(ctx)), "</div>"]
    return _stamp(_bar(ctx)) + "".join(body if len(body) > 1 else [_stamp(body[0])]) + _stamp(_dialog(ctx))


def _stamp(block: str) -> str:
    """Give a live block the digest of its HTML (`data-h`): the page swaps only blocks whose digest changed."""
    digest = hashlib.sha256(block.encode("utf-8")).hexdigest()[:12]
    return re.sub(r'data-k="([^"]*)"', lambda m: f'{m.group(0)} data-h="{digest}"', block, count=1)


def plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _default_subplan(rdir: Path, subplans: list[dict]) -> str:
    ids = [s["id"] for s in subplans]
    recent = next((ev["sp"] for ev in activity.events(rdir, 10) if ev.get("sp") in ids), "")
    return recent or next((s["id"] for s in subplans if s["ref"]), ids[0] if ids else "")


def text(ctx: dict, value: str, *, block: bool = False) -> str:
    """Escaped text in the chosen language; in EN + ES the original follows in muted type."""
    lang = ctx["opts"]["lang"]
    if lang == "en" or not value:
        return e(value)
    es = tr.phrase(ctx["cache"], value)
    if lang == "both" and es != value:
        return f'{e(es)}<span class="pp-orig{" block" if block else ""}" lang="en">{e(value)}</span>'
    return e(es)


def state_of(row: dict | None) -> tuple[str, str]:
    """(css class, label) of a subplan's design state."""
    if row is None:
        return "none", "sin interfaz"
    busy = row["status"] in drafts.ACTIVE
    if row["stale"] or (busy and row.get("reason") == "plan changed"):
        return "changed", "cambió · rediseñando" if busy or row["stale"] else "cambió"
    return row["status"], STATES.get(row["status"], row["status"])


def _seg(items: list[tuple[str, str, bool]], label: str) -> str:
    return (f'<nav class="pp-seg" aria-label="{e(label)}">' + "".join(
        f'<a href="{e(href)}" data-nav{" class=on aria-current=true" if on else ""}>{e(name)}</a>'
        for href, name, on in items) + "</nav>")


def _bar(ctx: dict) -> str:
    opts, rows, p, r = ctx["opts"], ctx["rows"], ctx["project"], ctx["rid"]
    mode = "doc" if opts["mode"] == "doc" else "subplans"
    modes = _seg([(link(p, r, opts, mode=k, rev=0), name, mode == k) for k, name in MODES], "Vista")
    langs = _seg([(link(p, r, opts, lang=k), name, opts["lang"] == k) for k, name in LANGS], "Idioma del plan")
    chips = []
    if opts["lang"] != "en":
        state = tr.status(ctx["rdir"])
        chips.append('<span class="pp-chip info">traduciendo…</span>' if state["running"] else
                     f'<span class="pp-chip warn">{state["pending"]} sin traducir</span>'
                     if state["pending"] else '<span class="pp-chip ok">traducción al día</span>')
    if rows:
        ready = sum(1 for row in rows.values() if row["status"] in ("ready", "approved") and not row["stale"])
        chips.append(f'<span class="pp-chip">diseños {ready}/{len(rows)}</span>')
    sources = [f for f in (ctx["rdir"] / "PLAN.md", ctx["rdir"] / "PLAN.json") if f.is_file()]
    when = (dt.datetime.fromtimestamp(max(f.stat().st_mtime for f in sources), dt.UTC).astimezone()
            if sources else None)
    live = f'<span class="pp-live" id="pl-live">en vivo{" · " + format(when, "%H:%M:%S") if when else ""}</span>'
    start = ""
    if rows and not drafts.active(ctx["rdir"]) and drafts.planning(ctx["rdir"]):
        start = (f'<form method="post" action="{purl(p, "req", r, "design-draft")}" class="pp-start"><input type="hidden" '
                 f'name="token" value="{e(ctx["token"])}"><input type="hidden" name="lang" value="{e(opts["lang"])}">'
                 f'<button type="submit" class="outline">Diseñar {plural(len(rows), "subplan", "subplanes")} con UI'
                 "</button></form>")
    return (f'<div class="pp-bar" data-k="bar">{modes}{langs}<div class="pp-chips">{"".join(chips)}</div>{live}'
            f'{start}{_approve_button(ctx)}</div>')


def _approve_button(ctx: dict) -> str:
    status = ctx["status"]
    if status in ("approved", "launched", "in-progress", "done"):
        return f'<span class="pp-chip ok">plan {e(status)}</span>'
    waiting = drafts.readiness(ctx["rdir"])
    label = f"Aprobar · {'falta' if len(waiting) == 1 else 'faltan'} {len(waiting)}" if waiting else "Aprobar plan"
    return f'<button type="button" class="pp-approve" data-open="pp-approve-dlg">{e(label)}</button>'


def _list(ctx: dict) -> str:
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    plan = drafts._plan(ctx["rdir"])
    milestones = {m.get("id"): m.get("title") or m.get("id") for m in plan.get("milestones") or [] if isinstance(m, dict)}
    owner = {item.get("id"): item.get("milestone_id") for item in plan.get("subplans") or [] if isinstance(item, dict)}
    items, last = [], None
    ui = sum(1 for s in ctx["subplans"] if s["ref"])
    moved = {ev.get("sp") for ev in activity.events(ctx["rdir"], 60)
             if ev.get("who") == "Planner" and _recent(ev.get("at"))}
    shown = [s for s in ctx["subplans"] if not opts["filter"] or (opts["filter"] == "ui" and s["ref"]) or
             (opts["filter"] == "changed" and (s["id"] in moved or (ctx["rows"].get(s["ref"]) or {}).get("stale")))]
    filters = "".join(f'<a href="{e(link(p, r, opts, filter=k))}" data-nav{" class=on aria-current=true" if opts["filter"] == k else ""}>'
                      f"{name}</a>" for k, name in (("", "Todos"), ("ui", "Con UI"), ("changed", "Cambiaron")))
    for s in shown:
        milestone = owner.get(s["id"])
        if milestone and milestone != last:
            items.append(f'<p class="pp-group">{e(str(milestone))} · {text(ctx, str(milestones.get(milestone, "")))}</p>')
            last = milestone
        cls, label = state_of(ctx["rows"].get(s["ref"]) if s["ref"] else None)
        on = s["id"] == opts["sp"]
        meta = plural(len(s["tasks"]), "tarea", "tareas") + (f" · {label}" if s["ref"] else "")
        items.append(f'<a class="pp-item{" on" if on else ""}" href="{e(link(p, r, opts, sp=s["id"], mode="subplans"))}"'
                     f' data-nav{" aria-current=true" if on else ""}><span class="pp-id">{e(s["id"])}</span>'
                     f'<span class="pp-item-main"><span class="pp-item-title" title="{e(s["title"])}">{text(ctx, s["title"])}</span>'
                     f'<span class="pp-meta">{e(meta)}</span></span>'
                     f'<span class="pp-dot {e(cls)}" title="{e(label)}"></span></a>')
    return (f'<nav class="pp-list" aria-label="Subplanes" data-k="list"><div class="pp-list-head"><strong>Subplanes'
            f'</strong><span class="pp-meta">{len(ctx["subplans"])} · {ui} con UI</span></div><nav class="pp-filters" '
            f'aria-label="Filtrar subplanes">{filters}</nav>{"".join(items) or "<p class=pp-meta>Ningún subplan en este filtro.</p>"}'
            "</nav>")


def _recent(stamp: str | None) -> bool:
    try:
        return time.time() - dt.datetime.fromisoformat(stamp or "").timestamp() <= activity.RECENT_SEC
    except ValueError:
        return False


def _detail(ctx: dict) -> str:
    import bt_page_planning_views as views
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    s = next(item for item in ctx["subplans"] if item["id"] == opts["sp"])
    row = ctx["rows"].get(s["ref"]) if s["ref"] else None
    cls, label = state_of(row)
    tabs = [("design", "Diseño"), ("tasks", f"Tareas ({len(s['tasks'])})"),
            ("criteria", f"Criterios ({len(s['criteria'])})")]
    nav = "".join(f'<a href="{e(link(p, r, opts, view=k))}" data-nav'
                  f'{" class=on aria-current=true" if opts["view"] == k else ""}>{e(name)}</a>' for k, name in tabs)
    if opts["view"] == "tasks":
        body = '<div class="pp-rows">' + "".join(
            f'<div class="pp-row"><span class="pp-id">{e(t.get("id", ""))}</span><span class="grow">'
            f'{text(ctx, t.get("title") or "")}</span><span class="pp-meta">{e(t.get("kind") or "")}'
            f'{" · UI" if t.get("ui") is True else ""}</span></div>' for t in s["tasks"]) + "</div>"
    elif opts["view"] == "criteria":
        body = "<ul class=pp-criteria>" + "".join(f"<li>{text(ctx, c)}</li>" for c in s["criteria"]
                                                  if isinstance(c, str)) + "</ul>"
    elif row is None:
        body = ('<p class="pp-empty">Este subplan no tiene interfaz: no lleva diseño. Sus tareas y criterios están en '
                'las otras pestañas.</p>')
    else:
        body = views.design_panel(ctx, s, row)
    return (f'<section class="pp-detail" data-k="detail-{e(s["id"])}-{e(opts["view"])}">'
            f'<header class="pp-dhead"><span class="pp-id lg">{e(s["id"])}</span><h2>{text(ctx, s["title"], block=True)}'
            f'</h2><span class="pp-state {e(cls)}">{e(label)}</span></header>'
            f'<p class="pp-outcome">{text(ctx, s["outcome"], block=True)}</p>'
            f'<nav class="pp-tabs" aria-label="Detalle del subplan">{nav}</nav>{body}</section>')


def _feed(ctx: dict) -> str:
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    tone = {"Planner": "changed", "Designer": "ready", "Tú → Designer": "accent", "Traducción": "info"}
    items = []
    for ev in activity.events(ctx["rdir"], 25):
        when = (ev.get("at") or "")[11:16]
        target = f' href="{e(link(p, r, opts, sp=ev["sp"], mode="subplans"))}" data-nav' if ev.get("sp") else ""
        tag = "a" if target else "div"
        diff = f'<span class="pp-diff">{e(ev["diff"])}</span>' if ev.get("diff") else ""
        items.append(f'<{tag} class="pp-ev"{target}><span class="pp-dot {tone.get(ev.get("who"), "none")}" '
                     f'aria-hidden="true"></span><span class="pp-ev-main"><span class="pp-meta">{e(when)} · '
                     f'{e(ev.get("who") or "")}</span><span>{e(ev.get("text") or "")}</span>{diff}</span></{tag}>')
    empty = '<p class="pp-meta">Aún no hay cambios: aparecerán aquí mientras planeas en la conversación.</p>'
    return (f'<aside class="pp-feed" aria-label="Lo que cambió en la conversación" data-k="feed">'
            f'<strong>Lo que cambió en la conversación</strong>{"".join(items) or empty}</aside>')


def _dialog(ctx: dict) -> str:
    status, p, r = ctx["status"], ctx["project"], ctx["rid"]
    if status in ("approved", "launched", "in-progress", "done"):
        return '<div data-k="dialog" hidden></div>'
    rows = []
    for s in ctx["subplans"]:
        row = ctx["rows"].get(s["ref"]) if s["ref"] else None
        cls, label = state_of(row)
        mark = {"ready": "✓", "approved": "✓", "none": "–", "failed": "!"}.get(cls, "…")
        detail = "sin interfaz · no lleva diseño" if row is None else f'{s["ref"]} · {label}'
        see = (f'<a href="{e(link(p, r, ctx["opts"], mode="review", sp=s["id"], rev=0))}" data-nav data-close>Ver diseño</a>'
               if row else "")
        rows.append(f'<div class="pp-check"><span class="pp-mark {e(cls)}" aria-hidden="true">{mark}</span>'
                    f'<span class="pp-id">{e(s["id"])}</span><span class="grow">{text(ctx, s["title"])}<span '
                    f'class="pp-meta block">{e(detail)}</span></span>{see}</div>')
    waiting = drafts.readiness(ctx["rdir"])
    review = status == "review"
    note = (f'<p class="pp-warn">{e("; ".join(waiting))}. El botón se activa cuando terminen.</p>' if waiting else
            "" if review else '<p class="pp-warn">El Planner todavía no deja el plan en revisión.</p>')
    disabled = " disabled" if waiting or not review else ""
    return (f'<dialog id="pp-approve-dlg" class="pp-dialog" data-k="dialog" aria-labelledby="pp-dlg-title">'
            f'<form method="post" action="{purl(p, "req", r, "plan")}"><input type="hidden" name="token" '
            f'value="{e(ctx["token"])}"><h2 id="pp-dlg-title">Aprobar plan y diseños</h2><p class="pp-meta">Al aprobar, '
            "cada diseño listo queda fijado como contrato v1 (SHA-256) y la ejecución lo usa tal cual: las tareas de "
            f'interfaz no vuelven a pausar.</p><div class="pp-checks">{"".join(rows)}</div>{note}'
            '<label class="pp-field">Comentarios (obligatorios si pides cambios)<textarea name="comments"></textarea>'
            '</label><div class="pp-actions"><button type="button" class="text" data-close>Cancelar</button>'
            f'<button type="submit" class="outline" name="decision" value="changes"{"" if review else " disabled"}>'
            f'Pedir cambios</button><button type="submit" name="decision" value="approve"{disabled}>Aprobar y lanzar'
            "</button></div></form></dialog>")


def plan_status(rdir: Path) -> str | None:
    plan = Path(rdir) / "PLAN.md"
    return _front(plan, "status") if plan.exists() else None
