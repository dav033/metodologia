"""Navigation indexes, regenerated (never hand-edited): one per project and one for the whole bitácora.

Project INDEX.md: quick links, workspace repos, requirements with their state, top pending (sorted), recent
decisions, artifacts and the timeline. Global ~/bitacora/INDEX.md: every project at a glance and what needs
attention. Both are refreshed at session end, on `bitacora.py index`, and when a project is created.
"""
from __future__ import annotations

from bt_core import *  # noqa: F403
from bt_core import _first_heading, _front

WEB = "http://127.0.0.1:8765"


def _requirements(pdir: Path) -> list[dict]:
    out = []
    for spec in sorted((pdir / "requirements").glob("REQ-*/SPEC.md")):
        rdir = spec.parent
        plan = rdir / "PLAN.md"
        rounds = list((rdir / "rounds").glob("round-*.json")) if (rdir / "rounds").exists() else []
        open_round = any('"status": "open"' in r.read_text(encoding="utf-8") for r in rounds)
        status = _front(spec, "status")
        if status == "?":  # hand-written specs: "Status: approved …" line instead of front matter
            m = re.search(r"^\**Status:?\**\s*:?\s*([A-Za-z-]+)", spec.read_text(encoding="utf-8"), re.M | re.I)
            status = m.group(1).lower() if m else "?"
        out.append({"id": req_id(rdir), "title": _first_heading(spec), "rel": spec.relative_to(pdir).as_posix(),
                    "spec": status, "plan": _front(plan, "status") if plan.exists() else "—",
                    "plan_rel": plan.relative_to(pdir).as_posix() if plan.exists() else "",
                    "report": (rdir / "REPORT.md").exists(), "open_round": open_round})
    return out


def _decisions(pdir: Path, n: int = 5) -> list[str]:
    text = (pdir / "DECISIONS.md").read_text(encoding="utf-8") if (pdir / "DECISIONS.md").exists() else ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    heads = re.findall(r"^## (D-\d{3,})\s*[—\-·:]\s*(.+?)\s*$", text, re.M)
    return [f"{d} — {t}" for d, t in heads[-n:]][::-1]


def _last_day(pdir: Path) -> str:
    days = sorted(pdir.glob("????-??/W*/????-??-??.md"))
    return days[-1].stem if days else "—"


def _attention(reqs: list[dict]) -> list[str]:
    out = []
    for r in reqs:
        if r["open_round"]:
            out.append(f"{r['id']}: question round waiting for answers")
        if r["plan"] == "review":
            out.append(f"{r['id']}: plan waiting for approval")
        if r["plan"] == "done" and r["report"]:
            out.append(f"{r['id']}: executor finished — review & merge")
        if r["plan"] == "changes-requested":
            out.append(f"{r['id']}: changes requested on the plan")
    return out


def project_index(pdir: Path) -> Path:
    import bt_pending
    project = pdir.name
    reqs = _requirements(pdir)
    lines = [f"# Index — {project}", "",
             f"_Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `bitacora.py index`. Do not edit by hand._", "",
             "**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · "
             "[Pending](PENDING.md) · [Tools](TOOLS.md)"
             + (" · [Glossary](GLOSSARY.md)" if (pdir / "GLOSSARY.md").exists() else "") + "  ",
             f"**Web:** [project]({WEB}/p/{project}) · [graph]({WEB}/p/{project}/graph)  ",
             f"**Last activity:** {_last_day(pdir)}", ""]
    repos = ws.repos(ROOT, project, discover=False)
    if repos:
        lines += ["## Workspace", ""] + [f"- **{role}** → `{p.as_posix()}`{'' if p.exists() else ' (not cloned here)'}"
                                         for role, p in repos.items()] + [""]
    attention = _attention(reqs)
    if attention:
        lines += ["## Needs attention", ""] + [f"- {a}" for a in attention] + [""]
    lines += ["## Requirements", ""]
    if reqs:
        lines += ["| ID | Title | Spec | Plan | |", "|---|---|---|---|---|"]
        for r in reqs:
            plan = f"[{r['plan']}]({r['plan_rel']})" if r["plan_rel"] else "—"
            extra = " · ".join(x for x in ("report ✓" if r["report"] else "", "round open" if r["open_round"] else "") if x)
            title = r["title"].split("—", 1)[-1].strip()
            lines.append(f"| [{r['id']}]({r['rel']}) | {title} | `{r['spec']}` | {plan} | {extra} |")
    else:
        lines.append("_None yet._")
    top = bt_pending.top(pdir, 7)
    lines += ["", "## Top pending (urgency, then complexity)", ""] + ([f"- {t}" for t in top] or ["_None._"])
    decs = _decisions(pdir)
    lines += ["", "## Recent decisions", ""] + ([f"- {d}" for d in decs] or ["_None yet._"])
    arts = sorted((pdir / "artifacts").glob("*.html")) if (pdir / "artifacts").exists() else []
    if arts:
        lines += ["", "## Artifacts", ""] + [f"- [{a.stem}]({WEB}/p/{project}/view/{a.name})" for a in arts]
    lines += ["", "## Timeline", ""]
    months = sorted([m for m in pdir.iterdir() if m.is_dir() and re.fullmatch(r"\d{4}-\d{2}", m.name)], reverse=True)
    if not months:
        lines.append("_No entries yet._")
    for m in months:
        lines.append(f"- **{m.name}** — [month summary]({m.name}/MONTH.md)")
        for w in sorted([w for w in m.iterdir() if w.is_dir()], reverse=True):
            days = sorted(w.glob("????-??-??.md"), reverse=True)
            day_links = ", ".join(f"[{d.stem[-2:]}]({d.relative_to(pdir).as_posix()})" for d in days)
            lines.append(f"  - [{w.name}]({w.relative_to(pdir).as_posix()}/WEEK.md): {day_links or '—'}")
    out = pdir / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def global_index() -> Path:
    import bt_pending
    projects = sorted(d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith(".")) if ROOT.exists() else []
    rows, attention = [], []
    for pdir in projects:
        reqs = _requirements(pdir)
        open_reqs = [r for r in reqs if r["spec"] not in ("done", "dropped")]
        top = bt_pending.top(pdir, 999)
        high = sum(1 for t in top if t.endswith(("high/S", "high/M", "high/L", "high/?")))
        repos = ", ".join(ws.repos(ROOT, pdir.name, discover=False)) or "—"
        rows.append(f"| [{pdir.name}]({pdir.name}/INDEX.md) | {repos} | {len(open_reqs)} | {len(top)} ({high} high) | "
                    f"{_last_day(pdir)} | [summary]({pdir.name}/SUMMARY.md) · [web]({WEB}/p/{pdir.name}) |")
        attention += [f"**{pdir.name}** — {a}" for a in _attention(reqs)]
    lines = ["# Bitácora — index", "",
             f"_Generated {dt.datetime.now():%Y-%m-%d %H:%M}. Do not edit by hand. Web: {WEB}_", "",
             "| Project | Repos | Open REQs | Open pending | Last activity | Links |", "|---|---|---|---|---|---|",
             *rows, ""]
    if attention:
        lines += ["## Needs attention", ""] + [f"- {a}" for a in attention] + [""]
    lines += ["## Shared", "", "- [Tools shared by several projects](TOOLS.md)", ""]
    out = ROOT / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
