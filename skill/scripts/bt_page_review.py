"""Review tab of a requirement: executor report, per-repo changes, coverage issues, merge / changes form."""
from __future__ import annotations

from html import escape as e

import bt_review as rv
import bt_trace as tr
from bt_core import *  # noqa: F403
from bt_core import _front
from bt_pages import badge, md, purl, read


def review_panel(project: str, rid: str, rdir: Path, token: str) -> str:
    plan_status = _front(rdir / "PLAN.md", "status") if (rdir / "PLAN.md").exists() else None
    report = rdir / "REPORT.md"
    parts = [f'<p>Plan: {badge(plan_status or "—")} · rama <code>{e(rv.feature_branch(rdir))}</code></p>']
    parts.append(md("report", read(report)) if report.exists() else
                 '<div class="notice warn">El ejecutor todavía no escribió <code>REPORT.md</code>.</div>')

    rows = []
    any_pending = False
    for role, st in rv.review_state(project, rdir).items():
        if not st.get("exists"):
            rows.append(f"<h3>{e(role)}</h3><p class='muted'>{e(st.get('note', ''))}</p>")
            continue
        if not st.get("branch"):
            rows.append(f"<h3>{e(role)}</h3><p class='muted'>Sin cambios para este requerimiento.</p>")
            continue
        any_pending |= not st["merged"]
        state = badge("done") + " fusionada" if st["merged"] else badge("review") + f" {len(st['commits'])} commits"
        dirty = (f'<div class="notice warn">Cambios sin commit en este repo ({len(st["dirty"])}): '
                 f'la fusión se bloquea hasta resolverlos.</div>' if st["dirty"] else "")
        commits = "".join(f"<li><code>{e(c)}</code></li>" for c in st["commits"][:20])
        stat = e("\n".join(st["stat"]))
        rows.append(f"<h3>{e(role)} · {state} → <code>{e(st['base'])}</code></h3>{dirty}"
                    f"<details><summary>Commits</summary><ul class='plain'>{commits}</ul></details>"
                    f"<details><summary>Archivos cambiados</summary><pre>{stat}</pre></details>")
    parts.append("<h2>Cambios por repo</h2>" + "".join(rows))

    issues = [i for i in tr.lint(tr.build(project, with_commits=False)) if i["node"].startswith(rid)]
    parts.append("<h2>Trazabilidad</h2>" + ("<ul class='plain'>" + "".join(
        f"<li>{badge('review')} {e(i['message'])}</li>" for i in issues) + "</ul>" if issues else
        "<p class='muted'>Cada requisito tiene su tarea.</p>"))

    if any_pending:
        parts.append(f"""<form class="q" method="post" action="{purl(project, 'req', rid, 'review')}">
<input type="hidden" name="token" value="{e(token)}">
<div class="question"><strong>Comentarios</strong> <span class="muted">(obligatorio si pides cambios)</span>
<textarea name="comments" aria-label="Comentarios"></textarea></div>
<div class="actions">
<button type="submit" name="decision" value="merge">Fusionar (local)</button>
<button type="submit" name="decision" value="merge_push">Fusionar y publicar (push)</button>
<button class="secondary" type="submit" name="decision" value="changes">Pedir cambios y relanzar ejecutor</button>
</div></form>""")
    return "".join(parts)
