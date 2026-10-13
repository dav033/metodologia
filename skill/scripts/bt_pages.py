"""HTML pages of the local bitácora server. Pure functions: data in, HTML string out."""
from __future__ import annotations

from html import escape as e
from urllib.parse import quote

import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_core import _first_heading, _front

OPEN_STATUSES = ("clarifying", "ready", "planned", "review", "approved", "launched", "in-progress",
                 "changes-requested")


def layout(title: str, body: str, crumbs: list[tuple[str, str]] | None = None) -> str:
    nav = " · ".join(f'<a href="{e(href)}">{e(label)}</a>' for label, href in (crumbs or []))
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · Bitácora</title>
<link rel="stylesheet" href="/static/style.css"></head><body>
<header class="top"><a class="brand" href="/">Bitácora</a><nav>{nav}</nav></header>
<main>{body}</main>
<script src="/static/marked.min.js"></script><script src="/static/app.js"></script></body></html>"""


def md(block_id: str, text: str) -> str:
    payload = json.dumps(text).replace("</", "<\\/")
    return (f'<div class="md" id="{block_id}"></div>'
            f'<script type="application/json" class="md-src" data-target="{block_id}">{payload}</script>')


def badge(status: str) -> str:
    return f'<span class="badge {e(status)}">{e(status)}</span>'


def read(f: Path) -> str:
    try:
        return f.read_text(encoding="utf-8")
    except Exception:
        return ""


def purl(project: str, *parts: str) -> str:
    return "/p/" + quote(project) + "".join("/" + quote(p) for p in parts)


# ---------------------------------------------------------------- data helpers

def projects() -> list[Path]:
    if not ROOT.exists():
        return []
    return sorted(d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith("."))


def requirements(pdir: Path) -> list[dict]:
    out = []
    for spec in sorted((pdir / "requirements").glob("REQ-*/SPEC.md")):
        rdir = spec.parent
        plan = rdir / "PLAN.md"
        open_round = rounds.open_round(rdir) if rounds.rounds_dir(rdir).exists() else None
        out.append({"id": req_id(rdir), "title": _first_heading(spec), "status": _front(spec, "status"),
                    "plan": _front(plan, "status") if plan.exists() else None, "open_round": open_round})
    return out


def open_pending(pdir: Path) -> list[str]:
    import bt_pending
    return bt_pending.top(pdir, 999)


def last_day_logs(pdir: Path, n: int = 7) -> list[Path]:
    return sorted(pdir.glob("????-??/W*/????-??-??.md"), reverse=True)[:n]


def artifacts(pdir: Path) -> list[Path]:
    d = pdir / "artifacts"
    return sorted((f for f in d.rglob("*") if f.is_file()), key=lambda f: f.stat().st_mtime, reverse=True) \
        if d.exists() else []


# ---------------------------------------------------------------- pages

def dashboard() -> str:
    cards = []
    for pdir in projects():
        reqs = requirements(pdir)
        active = [r for r in reqs if r["status"] in OPEN_STATUSES or (r["plan"] or "") in OPEN_STATUSES]
        waiting = [r for r in reqs if r["open_round"] or r["plan"] == "review"]
        days = last_day_logs(pdir, 1)
        repo = ", ".join(f"{r}: {p.name}" for r, p in ws.repos(ROOT, pdir.name).items())
        rows = "".join(
            f'<li><a href="{purl(pdir.name, "req", r["id"])}">{e(r["title"])}</a> {badge(r["plan"] or r["status"])}'
            f'{" <strong>· te espera</strong>" if r in waiting else ""}</li>' for r in active[:6])
        from bt_page_run import active_runs, fmt_age
        runs = "".join(
            f'<li>Maratón <a href="{purl(pdir.name, "req", m["req"])}?tab=run">{e(m["req"])}</a> {badge(m["status"])} '
            f'{m["done"]}/{m["total"]} · latido {fmt_age(m["age"])}'
            f'{" <strong>· ¿detenida?</strong>" if m["stale"] else ""}</li>' for m in active_runs(pdir))
        cards.append(f"""<div class="card"><h3><a href="{purl(pdir.name)}">{e(pdir.name)}</a></h3>
<div class="muted" style="font-size:13px">{e(repo) or "sin repos registrados"}</div>
<div class="kpis"><span class="kpi">{len(active)} activos</span><span class="kpi">{len(open_pending(pdir))} pendientes</span>
<span class="kpi">{len(artifacts(pdir))} artifacts</span>
<span class="kpi">último log: {e(days[0].stem) if days else "—"}</span></div>
<ul class="plain">{runs}{rows or '<li class="muted">Sin requerimientos activos</li>'}</ul></div>""")
    body = '<p style="float:right"><a href="/metrics">Métricas de agentes →</a></p><h1>Proyectos</h1>' + (f'<div class="grid">{"".join(cards)}</div>' if cards
                                   else '<p class="muted">Aún no hay proyectos en la bitácora.</p>')
    return layout("Proyectos", body)


PROJECT_TABS = [("summary", "Resumen"), ("requirements", "Requerimientos"), ("pending", "Pendientes"),
                ("decisions", "Decisiones"), ("architecture", "Arquitectura"), ("tools", "Herramientas"), ("timeline", "Bitácora"),
                ("artifacts", "Artifacts")]


def project_page(project: str, tab: str) -> str:
    pdir = ROOT / project
    tabs = "".join(f'<a class="{"on" if k == tab else ""}" href="{purl(project)}?tab={k}">{v}</a>'
                   for k, v in PROJECT_TABS) + f'<a href="{purl(project, "graph")}">Grafo ↗</a>'
    files = {"summary": "SUMMARY.md", "pending": "PENDING.md", "decisions": "DECISIONS.md",
             "architecture": "ARCHITECTURE.md", "tools": "TOOLS.md"}
    if tab in files:
        content = md("doc", read(pdir / files[tab]))
    elif tab == "requirements":
        rows = "".join(
            f'<tr><td><a href="{purl(project, "req", r["id"])}">{e(r["id"])}</a></td><td>{e(r["title"])}</td>'
            f'<td>{badge(r["status"])}</td><td>{badge(r["plan"]) if r["plan"] else "—"}</td>'
            f'<td>{"ronda abierta" if r["open_round"] else ""}</td></tr>' for r in requirements(pdir))
        content = (f"<table><tr><th>ID</th><th>Título</th><th>Spec</th><th>Plan</th><th></th></tr>{rows}</table>"
                   if rows else '<p class="muted">Sin requerimientos.</p>')
    elif tab == "timeline":
        items = []
        for m in sorted([m for m in pdir.glob("????-??") if m.is_dir()], reverse=True):
            items.append(f'<h3>{e(m.name)} · <a href="{purl(project, "doc", m.name, "MONTH.md")}">resumen del mes</a></h3>')
            for w in sorted([w for w in m.iterdir() if w.is_dir()], reverse=True):
                days = " ".join(f'<a href="{purl(project, "doc", m.name, w.name, d.name)}">{e(d.stem)}</a>'
                                for d in sorted(w.glob("????-??-??.md"), reverse=True))
                items.append(f'<p><a href="{purl(project, "doc", m.name, w.name, "WEEK.md")}">{e(w.name)}</a>: '
                             f'{days or "—"}</p>')
        content = "".join(items) or '<p class="muted">Sin entradas.</p>'
    else:  # artifacts
        rows = "".join(
            f'<li><a href="{purl(project, "view", *f.relative_to(pdir / "artifacts").parts)}">'
            f'{e(f.relative_to(pdir / "artifacts").as_posix())}</a> '
            f'<span class="muted">· {dt.datetime.fromtimestamp(f.stat().st_mtime):%Y-%m-%d %H:%M}</span></li>'
            for f in artifacts(pdir))
        content = f'<ul class="plain">{rows}</ul>' if rows else (
            '<p class="muted">Sin artifacts. Los agentes los guardan en '
            f'<code>{e((pdir / "artifacts").as_posix())}</code>.</p>')
    body = f'<h1>{e(project)}</h1><div class="tabs">{tabs}</div><div class="panel">{content}</div>'
    return layout(project, body, [(project, purl(project))])


def doc_page(project: str, rel: str) -> str:
    f = ROOT / project / rel
    body = f'<p class="muted">{e(rel)}</p>' + md("doc", read(f))
    return layout(rel, body, [(project, purl(project))])


def artifact_view(project: str, rel: str) -> str:
    raw = purl(project, "artifacts", *rel.split("/"))
    body = (f'<div class="actions" style="justify-content:space-between"><h1>{e(rel)}</h1>'
            f'<a href="{raw}" target="_blank">abrir solo ↗</a></div>'
            f'<iframe class="artifact" src="{raw}" sandbox="allow-scripts allow-popups"></iframe>')
    return layout(rel, body, [(project, purl(project)), ("artifacts", purl(project) + "?tab=artifacts")])
