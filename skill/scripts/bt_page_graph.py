"""Trace graph page (Cytoscape) and the per-requirement coverage matrix."""
from __future__ import annotations

from html import escape as e

import bt_trace as tr
from bt_core import *  # noqa: F403
from bt_pages import layout, purl

TYPES = [("REQ", "Requerimientos"), ("US", "Historias"), ("R", "Requisitos"), ("T", "Tareas"),
         ("D", "Decisiones"), ("P", "Pendientes"), ("C", "Commits"), ("F", "Archivos")]


def graph_page(project: str) -> str:
    g = tr.build(project)
    issues = tr.lint(g)
    payload = json.dumps(g.to_dict(), ensure_ascii=False).replace("</", "<\\/")
    toggles = "".join(f'<label class="kpi"><input type="checkbox" data-type-toggle="{t}"> '
                      f'<span class="dot" style="background:var(--g-{t})"></span>{label}</label>'
                      for t, label in TYPES)
    lint_rows = "".join(
        f'<li><span class="badge {"changes-requested" if i["level"] == "error" else "review"}">{e(i["code"])}</span> '
        f'<a href="#" data-focus="{e(i["node"])}">{e(i["message"])}</a></li>' for i in issues) \
        or '<li class="muted">Sin problemas: cada requisito tiene tarea y no hay referencias rotas.</li>'
    counts = {}
    for n in g.nodes.values():
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    summary = " · ".join(f"{counts.get(t, 0)} {label.lower()}" for t, label in TYPES if counts.get(t))
    body = f"""<h1>Grafo · {e(project)}</h1>
<p class="muted">{e(summary) or "Sin nodos todavía"} — derivado de los IDs de la bitácora y de los commits que los citan.
Clic en un nodo: su vecindario. Busca un ID (REQ-001, D-004) o texto.</p>
<div class="actions" style="margin:8px 0">{toggles}
<input id="graph-search" type="text" placeholder="Buscar ID o texto y Enter" style="max-width:260px"></div>
<div class="graph-wrap"><div id="graph"></div><aside class="card" id="node-info"><p class="muted">Selecciona un nodo.</p></aside></div>
<h2>Chequeo de trazabilidad</h2><ul class="plain">{lint_rows}</ul>
<script type="application/json" id="graph-data">{payload}</script>
<script src="/static/cytoscape.min.js"></script><script src="/static/graph.js"></script>"""
    return layout(f"Grafo {project}", body, [(project, purl(project)), ("grafo", purl(project, "graph"))])


def coverage_panel(project: str, rid: str) -> str:
    """R/US × tasks matrix for one requirement, plus the commits that cite it."""
    g = tr.build(project)
    reqs = [n for n in g.nodes.values() if n["type"] in ("R", "US") and n.get("req") == rid]
    tasks = [n for n in g.nodes.values() if n["type"] == "T" and n.get("req") == rid]
    if not reqs and not tasks:
        return '<p class="muted">El spec aún no tiene requisitos (R1…) ni historias (US-1…), o no hay plan.</p>'
    covers = {(e_["source"], e_["target"]) for e_ in g.edges if e_["type"] == "covers"}
    head = "".join(f'<th title="{e(t["label"])}">{e(t["id"].split("/")[-1])}{"✓" if t.get("done") else ""}</th>'
                   for t in tasks)
    rows = []
    for r in sorted(reqs, key=lambda n: (n["type"], int(re.sub(r"\D", "", n["id"].split("/")[-1]) or 0))):
        cells = "".join("<td>●</td>" if (t["id"], r["id"]) in covers else "<td></td>" for t in tasks)
        hit = any((t["id"], r["id"]) in covers for t in tasks)
        rows.append(f'<tr><td>{"" if hit else "⚠ "}{e(r["label"])}</td>{cells}</tr>')
    commits = [g.nodes[e_["source"]] for e_ in g.edges if e_["target"] == rid and e_["type"] == "refs"]
    commit_list = "".join(f'<li><code>{e(c["id"])}</code> {e(c["label"])} <span class="muted">{e(c.get("date", ""))}</span></li>'
                          for c in commits) or '<li class="muted">Ningún commit cita este requerimiento todavía.</li>'
    return (f'<div style="overflow-x:auto"><table class="matrix"><tr><th>Requisito / historia</th>{head}</tr>'
            f'{"".join(rows)}</table></div><p class="muted">● la tarea lo cubre · ⚠ nadie lo cubre · ✓ tarea hecha</p>'
            f'<h3>Commits que lo citan</h3><ul class="plain">{commit_list}</ul>'
            f'<p><a href="{purl(project, "graph")}">Ver en el grafo →</a></p>')
