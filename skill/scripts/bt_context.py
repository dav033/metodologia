"""`bitacora.py context`: everything an agent needs to act on its own, in one screen.

Who is available (models, accounts, quotas), how work is routed and escalated, how to delegate to another agent, what
was learned about the project and its owner, what the measured results say, and where the documents live. The same
blocks are injected into supervised sessions; this command is the on-demand copy for any agent in any CLI.
"""
from __future__ import annotations

import bt_agents
import bt_events
from bt_core import *  # noqa: F403

SKILL = SKILL_DIR  # resolved by bt_core.resource_root(): checkout, override or installed package


def text(project: str | None) -> str:
    cli = f'"{PYTHON}" "{SCRIPT.as_posix()}"' + (f" --project {project}" if project else "")
    out = [f"# Agent context{' — ' + project if project else ''}", "", bt_agents.brief(project), "",
           "### Routing (what runs where, decided by the supervisor, not by habit)",
           "- Tier 0 light, 1 standard, 2 top. A task starts at 0 (`level: architecture` -> 2, audits -> 1); each "
           "failed attempt climbs one tier, and prefers ANOTHER provider than the one that failed.",
           "- Kinds: implement, test, docs, audit, research (PLAN line `kind:`, else inferred from the title). An "
           "audit goes to another provider than the builder's.",
           "- An account that reports a usage limit is skipped until its reset; work continues on the others. Only "
           "when every account is cooling down does a run wait.",
           "- Among equal candidates: best measured success rate for that kind, then the least used account.",
           "", "### Delegate (any agent to any agent)",
           f"- Let the router choose: `{cli} delegate start \"<task>\" --kind audit --verify \"<cmd>\"`",
           f"- Pin it: `{cli} delegate start \"<task>\" --profile <id> --model <model> --effort <low|medium|high|xhigh|max>`",
           "- `--allow <path>` limits what it may change; `--background` returns an id (`delegate status <id>`). The "
           "result is compact and checked: `verified` only when the verify command passed, `claimed` is just its word.",
           f"- Which route would be used: `{cli} agents route --kind test --tier 1` · accounts and limits: `{cli} agents`",
           "", "### Learning",
           f"- Propose: `{cli} learn add \"<sentence>\" --evidence \"<observed>\" --source REQ-NNN/Tn "
           "[--scope project|owner|skill] [--kind preference|convention|pitfall|tooling|decision]`",
           f"- Review: `{cli} learn list [--status candidate]` · owner decides: `learn confirm|reject L-NNN`. A "
           "candidate seen from 3 independent sources is promoted on its own."]
    import bt_learn
    learned = bt_learn.context_brief(project)
    if learned:
        out += ["", learned]
    from bt_continuation import continuation_context
    continuation = continuation_context(ROOT, project)
    if continuation:
        out += ["", continuation]
    out += ["", "### What the measurements say", *[f"- {line}" for line in bt_events.advice(bt_events.read_all(), defects=bt_events.read_defects())],
            f"- Full table: `{cli} metrics --by agent,model,effort,kind`", "", "### Where things are"]
    out += ["", "### Foreground milestone entry (REQ-008)",
            f"- Approved planning transition: `{cli} handoff REQ-NNN --foreground --planning-session <id>`.",
            f"- Manual checkout entry: `{cli} run REQ-NNN --foreground --no-autostart`.",
            ("- Requires a verified relay parent for automatic replacement and a bounded reasoning/action runtime. "
             "T3 provides the lifecycle; T4 activation is pending. Unsupported capacity never falls back to native tools.")]
    if project:
        pdir = ROOT / project
        for label, f in (("Summary", "SUMMARY.md"), ("Architecture", "ARCHITECTURE.md"), ("Decisions", "DECISIONS.md"),
                         ("Pending", "PENDING.md"), ("Learnings", "LEARNINGS.md"), ("Tools", "TOOLS.md"),
                         ("Index", "INDEX.md")):
            if (pdir / f).exists():
                out.append(f"- {label}: `{(pdir / f).as_posix()}`")
    for label, f in (("Skill router", "SKILL.md"), ("Agents and routing", "references/agents.md"),
                     ("Requirements and hand-off", "references/requirements.md"),
                     ("Execution", "references/execution.md"), ("Marathon", "references/marathon.md"),
                     ("Self-improvement", "references/self-improvement.md")):
        if (SKILL / f).exists():
            out.append(f"- {label}: `{(SKILL / f).as_posix()}`")
    return "\n".join(out)
