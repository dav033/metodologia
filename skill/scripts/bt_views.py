"""Bitácora views: generated INDEX.md, pending rollups, SessionStart context."""
from __future__ import annotations

from bt_core import *  # noqa: F403
from bt_core import _front
# ---------------------------------------------------------------- rollups

def pending_rollups(pdir: Path) -> list[str]:
    """Week/month summaries of *past* periods that are still drafts."""
    todo = []
    cur = day_paths(pdir, today())
    for f in sorted(pdir.glob("????-??/MONTH.md")) + sorted(pdir.glob("????-??/W*/WEEK.md")):
        if f in (cur["month"], cur["week"]):
            continue
        if "status: draft" in f.read_text(encoding="utf-8"):
            todo.append(f.relative_to(pdir).as_posix())
    return todo


# ---------------------------------------------------------------- context (SessionStart)

def _section(text: str, heading: str, max_lines: int = 25) -> str:
    m = re.search(rf"^## {re.escape(heading)}.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return ""
    body = [l for l in m.group(1).strip().splitlines()
            if l.strip() and l.strip() != "-" and not re.fullmatch(r"_[^_].*_", l.strip())]  # skip template placeholders
    return "\n".join(body[:max_lines])


def last_next_steps(pdir: Path) -> str:
    days = sorted(pdir.glob("????-??/W*/????-??-??.md"), reverse=True)
    for d in days[:5]:
        text = d.read_text(encoding="utf-8")
        blocks = re.findall(r"### Next session starts with\s*\n(.*?)(?=\n### |\n---|\Z)", text, re.S)
        for b in reversed(blocks):
            b = "\n".join(l for l in b.strip().splitlines() if l.strip() and not l.strip().startswith("<!--"))
            if b and b.strip() not in ("-", "1."):
                return f"(from {d.stem})\n{b}"
    return ""


def build_context(project: str | None, session_id: str, cwd: Path, source: str) -> str:
    skill_hint = ("Follow the `metodologia` skill for this whole session (requirements, engineering, bitácora). "
                  "Talk to the user in Spanish; bitácora files in English; code in the repo's language.")
    if in_hq(cwd) and not project:
        return f"[bitácora] {skill_hint}\n" + hq_overview(session_id)
    if not project:
        known = [d.name for d in sorted(ROOT.iterdir()) if d.is_dir() and not d.name.startswith(".")] \
            if ROOT.exists() else []
        workspaces = "\n".join(f"- **{p}**: {ws.describe(ROOT, p)}" for p in known) or "- (none yet)"
        return (f"[bitácora] {skill_hint}\n"
                f"No project detected yet for cwd `{cwd}` — this folder spans several projects. Known workspaces:\n"
                f"{workspaces}\n"
                f"As soon as the user's request is about one of them (or a new one), bind this session — don't ask "
                f"if it's obvious from the request or the files involved:\n"
                f"  python \"{SCRIPT.as_posix()}\" bind {session_id} <project>\n"
                f"(Touching files inside a workspace repo also binds the session automatically at the next stop.)\n"
                f"session_id: {session_id}")
    pdir, created = ensure_project(project)
    if source in ("startup", "clear", "bind"):
        day = ensure_session_block(pdir, session_id, cwd)
    else:
        day = ensure_day(pdir, today())["day"]
    paths = day_paths(pdir, today())
    out = [f"[bitácora] {skill_hint}",
           f"Project: **{project}** → `{pdir.as_posix()}` · workspace repos: {ws.describe(ROOT, project)}",
           f"Today's log (your session section is `{session_id[:8]}`): `{day.as_posix()}`",
           f"Week summary: `{paths['week'].as_posix()}` · Month summary: `{paths['month'].as_posix()}`",
           f"Script: python \"{SCRIPT.as_posix()}\" <cmd>   (cmds: where, id D|P|REQ, req new, index, rollups)"]
    try:  # supervised marathon session: whatever the source (startup, compact…), restate the one task at hand
        from bt_runprompt import marathon_block
        if block := marathon_block():
            out += ["", block]
    except Exception:
        pass
    if in_hq(cwd):
        repo = ws.describe(ROOT, project)
        out.append(f"HQ MODE (planning room): do requirements → spec → plan here; read the code at "
                   f"{repo} (register more with `workspace add <role> <path>`); do NOT edit the repo from "
                   f"here. Once the user approves the plan, launch the executor: "
                   f"python \"{SCRIPT.as_posix()}\" --project {project} launch REQ-NNN [--agent codex] "
                   f"(see references/execution.md §1c).")
    tools, shared = tool_names(pdir / "TOOLS.md"), tool_names(ROOT / "TOOLS.md")
    out.append(f"Tools & infra (TOOLS.md): {', '.join(tools) or 'none registered'}"
               f"{' · shared: ' + ', '.join(shared) if shared else ''} — read references/tools.md before using them.")
    if created:
        out.append("NEW PROJECT: bootstrap SUMMARY.md and ARCHITECTURE.md from the repo/context before or "
                   "alongside the first task (see references/documentation.md §Bootstrap).")
    if source == "compact":
        out.append("Context was just compacted: re-read today's log before continuing, and log anything "
                   "important from before the compaction that isn't there yet.")
    summ = (pdir / "SUMMARY.md").read_text(encoding="utf-8")
    state = _section(summ, "Current state", 12)
    if state:
        out += ["", "### Current state (SUMMARY.md)", state]
    import bt_pending
    bt_pending.sort_file(pdir)
    top = bt_pending.top(pdir, 5)
    if top:
        out += ["", "### Top pending (PENDING.md, sorted by urgency then complexity)", *[f"- {t}" for t in top]]
    unsized = (pdir / "PENDING.md").read_text(encoding="utf-8").count("complexity: ?")
    if unsized:
        out.append(f"({unsized} pending item(s) have no complexity estimate yet: when you touch this project, "
                   f"estimate them S/M/L in PENDING.md — the file re-sorts itself.)")
    blocked = _section((pdir / "PENDING.md").read_text(encoding="utf-8"), "Blocked", 6)
    if blocked and "_None_" not in blocked:
        out += ["", "### Pending — Blocked", blocked]
    nxt = last_next_steps(pdir)
    if nxt:
        out += ["", "### Last session said to start with", nxt]
    roll = pending_rollups(pdir)
    if roll:
        out += ["", "### Rollups due (finalize these past summaries early in the session)"] + [f"- {r}" for r in roll]
    return "\n".join(out)


def hq_overview(session_id: str) -> str:
    lines = ["HQ MODE (planning room) at the bitácora root. Projects:"]
    projects = sorted(d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith("."))
    if not projects:
        lines.append("- (none yet)")
    for d in projects:
        repo = ws.describe(ROOT, d.name)
        open_reqs = [f"{s.parent.name.split('-')[0]}-{s.parent.name.split('-')[1]} ({_front(s, 'status')})"
                     for s in sorted((d / "requirements").glob("REQ-*/SPEC.md"))
                     if _front(s, "status") not in ("done", "dropped")]
        lines.append(f"- **{d.name}** · {repo} · open: {', '.join(open_reqs) or 'none'}")
    lines += ["When the user names the project (or a new one), bind this session to it:",
              f"  python \"{SCRIPT.as_posix()}\" bind {session_id} <project>",
              "Then: requirements → spec → plan → user approval → `launch` (references/execution.md §1c).",
              f"session_id: {session_id}"]
    return "\n".join(lines)
