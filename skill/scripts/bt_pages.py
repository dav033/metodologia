"""HTML pages of the local bitácora server. Pure functions: data in, HTML string out."""
from __future__ import annotations

import re
from html import escape as e
from urllib.parse import quote

import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_core import _first_heading, _front

OPEN_STATUSES = ("clarifying", "ready", "planned", "review", "approved", "launched", "in-progress",
                 "changes-requested")


# `?theme=light|dark` forces a theme, so screenshots of both are reproducible (headless browsers always render dark)
THEME_JS = ("var t=new URLSearchParams(location.search).get('theme');"
            "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;"
            "var d=t==='dark'||(t!=='light'&&window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);"
            "document.documentElement.classList.toggle('sl-theme-dark',d);")
SHOELACE = "/static/vendor/shoelace-2.20.1"       # vendored web components (MIT, see its LICENSE.md): no CDN at runtime


def layout(title: str, body: str, crumbs: list[tuple[str, str]] | None = None) -> str:
    nav = '<span class="sep">/</span>'.join(f'<a href="{e(href)}">{e(label)}</a>' for label, href in (crumbs or []))
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · Bitácora</title>
<script>{THEME_JS}</script>
<link rel="stylesheet" href="{SHOELACE}/themes/light.css"><link rel="stylesheet" href="{SHOELACE}/themes/dark.css">
<link rel="stylesheet" href="/static/style.css">
<script type="module" src="{SHOELACE}/shoelace-autoloader.js"></script></head><body>
<header class="top"><a class="brand" href="/">Bitácora</a><nav>{nav}</nav>
<nav class="mainnav" aria-label="Secciones"><a href="/plans">Planes</a><a href="/now">Ahora</a><a href="/flow">Flujo</a><a href="/metrics">Métricas</a></nav></header>
<div class="nowbar" id="nowbar" hidden></div>
<main>{body}</main>
<script src="/static/marked.min.js"></script><script src="/static/app.js"></script>
<script src="/static/live.js"></script></body></html>"""


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

def _req_title(title: str) -> str:
    return re.sub(r"^REQ-\d+\s*[—–:-]\s*", "", title or "") or title


def dashboard() -> str:
    from bt_page_run import active_runs, fmt_age
    cards, total_active = [], 0
    for pdir in projects():
        reqs = requirements(pdir)
        active = [r for r in reqs if r["status"] in OPEN_STATUSES or (r["plan"] or "") in OPEN_STATUSES]
        total_active += len(active)
        waiting = [r for r in reqs if r["open_round"] or r["plan"] == "review"]
        days = last_day_logs(pdir, 1)
        repos = [f"{r}: {p.name}" for r, p in ws.repos(ROOT, pdir.name).items()]
        repo = (f"{len(repos)} repos" if len(repos) > 3 else ", ".join(repos)) or "sin repos registrados"
        rows = "".join(
            f'<div class="it{" flag" if r in waiting else ""}"><span class="id">{e(r["id"])}</span>'
            f'<a class="t" href="{purl(pdir.name, "req", r["id"])}">{e(_req_title(r["title"]))}</a>'
            f'{badge(r["plan"] or r["status"])}</div>' for r in active[:5])
        runs = "".join(
            f'<div class="it"><span class="id">{e(m["req"])}</span>'
            f'<a class="t" href="{purl(pdir.name, "req", m["req"])}?tab=run">Ejecución {m["done"]}/{m["total"]} · '
            f'latido {fmt_age(m["age"])}{" · ¿detenida?" if m["stale"] else ""}</a>{badge(m["status"])}</div>'
            f'{("<code>bitacora.py --project " + e(pdir.name) + " scheduler-run " + e(m["req"]) + " --resume</code>"
               if m["stale"] and m.get("authority") == "scheduler" else "")}' for m in active_runs(pdir))
        more = f'<a class="muted" href="{purl(pdir.name)}?tab=requirements">y {len(active) - 5} más →</a>' if len(active) > 5 else ""
        cards.append(f"""<article class="card pcard"><h3><a href="{purl(pdir.name)}">{e(pdir.name)}</a></h3>
<div class="repo" title="{e(", ".join(repos))}">{e(repo)}</div>
<div class="kpis"><span class="kpi">{len(active)} activos</span><span class="kpi">{len(open_pending(pdir))} pendientes</span>
<span class="kpi">{len(artifacts(pdir))} artifacts</span></div>
<div class="dots">{runs}{rows or '<p class="muted" style="margin:0">Sin requerimientos activos</p>'}</div>{more}
<div class="foot">último log: {e(days[0].stem) if days else "—"}</div></article>""")
    head = (f'<div class="head"><div><p class="eyebrow">{len(cards)} proyectos · {total_active} requerimientos activos</p>'
            '<h1>Proyectos</h1></div><div class="side"><a href="/plans">Planes →</a>'
            '<a href="/metrics">Métricas de agentes →</a></div></div>')
    body = head + (f'<div class="grid">{"".join(cards)}</div>' if cards
                   else '<p class="muted">Aún no hay proyectos en la bitácora.</p>')
    return layout("Proyectos", body)


PROJECT_TABS = [("overview", "General"), ("plans", "Planes"), ("requirements", "Requerimientos"), ("pending", "Pendientes"),
                ("decisions", "Decisiones"), ("summary", "Resumen"), ("architecture", "Arquitectura"), ("tools", "Herramientas"),
                ("timeline", "Bitácora"), ("artifacts", "Artifacts")]


def _project_plan_rows(project: str) -> list[dict]:
    import bt_planstatus
    return [r for r in bt_planstatus.list_plans(ROOT) if r["project"] == project]


SECTION_ES = {"open": "Abiertos", "recently closed": "Cerrados recientemente", "blocked": "Bloqueados"}
URGENCY_ES = {"high": "alta", "med": "media", "low": "baja"}


def _pending_view(pdir: Path) -> str:
    """PENDING.md as a list: id, title, urgency/complexity chips, source line; the details stay folded."""
    import bt_pending
    f = pdir / "PENDING.md"
    if not f.exists():
        return '<p class="muted">Sin pendientes.</p>'
    sections, _ = bt_pending.parse(f.read_text(encoding="utf-8"))
    out = []
    for name, items in sections.items():
        if not items:
            continue
        rows = []
        for it in items:
            urg = it["urgency"] if it["explicit"].get("urgency") else ""
            chips = (f'<span class="ch u-{e(urg)}">{e(URGENCY_ES.get(urg, urg))}</span>' if urg else "") + (
                f'<span class="ch">{e(it["complexity"])}</span>' if it["explicit"].get("complexity") else "")
            title = re.sub(r"^CLOSED \d{4}-\d{2}-\d{2}\s*[—-]\s*", "", it["title"])
            meta = " · ".join(it["others"])
            lines = [re.sub(r"^\s*[-*]\s*", "", ln) for ln in it["details"] if ln.strip()] if it["details"] else []
            detail = (f'<details><summary>Detalle</summary>{"".join(f"<p>{e(ln)}</p>" for ln in lines)}</details>'
                      if lines else "")
            rows.append(f'<div class="pi{" closed" if it["done"] else ""}" id="{e(it["id"])}"><span class="id">{e(it["id"])}</span>'
                        f'<div><div class="pt">{e(title)}</div>{f"<div class=pm>{e(meta)}</div>" if meta else ""}{detail}</div>'
                        f'<div class="chs">{chips}</div></div>')
        label = SECTION_ES.get(name.lower(), name)
        body = f'<div class="pend">{"".join(rows)}</div>'
        if name.lower() == "open":
            out.append(f'<div class="sub">{e(label)} · {len(items)}</div>{body}')
        else:
            out.append(f'<details class="fin"><summary>{e(label)} ({len(items)})</summary>{body}</details>')
    return f'<div class="pl">{"".join(out)}</div>{__import__("bt_page_plans").CSS}'


def _overview(project: str, pdir: Path) -> str:
    """Short landing view: what is open, what is pending, where the activity is. The long documents live in their tabs."""
    import bt_page_plans as pp
    link = lambda tab, text: f'<a class="go" href="{purl(project)}?tab={tab}">{text} →</a>'  # noqa: E731
    plans = pp.project_plans(_project_plan_rows(project), limit=5)
    pending = open_pending(pdir)
    items = "".join(
        f'<div class="it"><span class="id">{e(p.split(" · ")[0])}</span><span class="t">{e(p.split(" · ")[1])}</span>'
        f'<span class="kpi">{e(p.split(" · ")[-1])}</span></div>' for p in pending[:5] if p.count(" · ") >= 2)
    days = last_day_logs(pdir, 1)
    reqs = requirements(pdir)
    active = [r for r in reqs if r["status"] in OPEN_STATUSES or (r["plan"] or "") in OPEN_STATUSES]
    stats = (f'<span class="kpi">{len(active)} {"requerimiento activo" if len(active) == 1 else "requerimientos activos"}</span><span class="kpi">{len(pending)} pendientes</span>'
             f'<span class="kpi">{len(artifacts(pdir))} artifacts</span>')
    return (f'<div class="grid ov"><article class="card wide"><h3>Planes abiertos</h3>{plans}{link("plans", "Ver todos los planes")}</article>'
            f'<article class="card"><h3>Pendientes</h3><div class="dots">{items or "<p class=muted>Nada pendiente.</p>"}</div>'
            f'{link("pending", "Ver pendientes")}</article>'
            f'<article class="card"><h3>Actividad</h3><div class="kpis">{stats}</div>'
            f'<p class="muted" style="margin:0">Último log: {e(days[0].stem) if days else "—"}</p>{link("timeline", "Ver la bitácora")}</article></div>')


def project_page(project: str, tab: str = "overview") -> str:
    pdir = ROOT / project
    shown = list(PROJECT_TABS) + ([("glossary", "Glosario")] if (pdir / "GLOSSARY.md").exists() else [])
    tabs = "".join(f'<a class="{"on" if k == tab else ""}" href="{purl(project)}?tab={k}">{v}</a>'
                   for k, v in shown) + f'<a href="{purl(project, "graph")}">Grafo ↗</a>'
    files = {"summary": "SUMMARY.md", "pending": "PENDING.md", "decisions": "DECISIONS.md",
             "architecture": "ARCHITECTURE.md", "tools": "TOOLS.md", "glossary": "GLOSSARY.md"}
    if tab == "overview":
        content = _overview(project, pdir)
    elif tab == "pending":
        content = _pending_view(pdir)
    elif tab == "plans":
        import bt_page_plans as pp
        content = pp.project_plans(_project_plan_rows(project))
    elif tab in files:
        text = read(pdir / files[tab])
        content = md("doc", text) if text.strip() else '<p class="muted">Todavía no hay nada en este documento.</p>'
    elif tab == "requirements":
        rows = "".join(
            f'<tr><td><a href="{purl(project, "req", r["id"])}">{e(r["id"])}</a></td><td>{e(_req_title(r["title"]))}</td>'
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
    body = (f'<div class="head"><div><p class="eyebrow">proyecto</p><h1>{e(project)}</h1></div></div>'
            f'<div class="tabs">{tabs}</div>'
            + (content if tab == "overview" else f'<div class="panel">{content}</div>'))
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
