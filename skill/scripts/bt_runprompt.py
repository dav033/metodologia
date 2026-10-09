"""Marathon prompts: what a fresh headless session is told, how the agent command is built, and the
"Current marathon task" block the SessionStart hook re-injects (also after a compaction)."""
from __future__ import annotations

import shutil

from bt_core import *  # noqa: F403
import bt_runstate as rs

FINAL_TASK = "FINAL"


def _paths(project: str, rdir: Path) -> list[str]:
    pdir = ROOT / project
    lines = []
    for label, f in (("HANDOFF", rdir / "HANDOFF.md"), ("Spec", rdir / "SPEC.md"), ("Plan", rdir / "PLAN.md"),
                     ("SUMMARY", pdir / "SUMMARY.md"), ("ARCHITECTURE", pdir / "ARCHITECTURE.md"),
                     ("TOOLS", pdir / "TOOLS.md")):
        if f.exists():
            lines.append(f"- {label}: `{f.as_posix()}`")
    return lines


def _bundle(project: str, req: str) -> str:
    try:
        import bt_trace as tr
        return tr.bundle(tr.build(project, with_commits=False), req, 2, 25)
    except Exception:
        return ""


def _recent_log(state: dict, task_id: str, n: int = 5) -> list[str]:
    rows = [e for e in state.get("log", []) if e.get("task") == task_id][-n:]
    return [f"- session {e['session']} {e['result']}: {e['summary']}" for e in rows]


def _rules(project: str, req: str, task_id: str, branch: str) -> list[str]:
    cli = f'python "{SCRIPT.as_posix()}" --project {project}'
    return [
        "## Rules (non-negotiable)",
        "- This is a headless session started by a supervisor: nobody answers questions. Decide, record a ruling "
        "in PLAN.md, keep going. Start no message with `Aye`; do not write a final report for the user.",
        f"- Work ONLY on task {task_id}. Do not start other tasks, do not refactor outside its scope.",
        "- Follow references/engineering.md of the `metodologia` skill and run the antagonist review "
        "(references/subagents.md) before EVERY commit.",
        f"- Commit on the feature branch `{branch}` of the repo you touch (create it if missing). NEVER push, "
        "deploy or publish.",
        "- Use subagents for noisy work (long searches, test output, logs) so this context stays small.",
        f"- When finished, run exactly one of:\n  `{cli} task done {req} {task_id} --evidence \"<what proves it>\"`\n"
        f"  `{cli} task fail {req} {task_id} --reason \"<why it cannot be done>\"` "
        "(add `--blocked` if it needs a human decision or secret).",
        f"- Leave advice for the next attempt with `{cli} task note {req} {task_id} --text \"...\"`.",
        "- Log this session in today's day log of the bitácora (Done / Decisions / Not done / Next).",
    ]


def session_prompt(project: str, rdir: Path, state: dict, task: dict | None, session: int, branch: str) -> str:
    req = state["req"]
    ultra = ["", "ultracode: use the Workflow tool for substantive multi-step work in this task"] \
        if state.get("ultracode") else []
    if task is None:  # final session
        head = [f"# Marathon {project} {req} — FINAL session {session}",
                "Every task is done. Do the closing work of references/execution.md §4:",
                "- fresh-eyes review (reviewer subagents: spec + standards) over the whole diff of the feature branch; "
                "fix only correctness problems, defer the rest to PENDING.md;",
                "- run the plan's Verification for real and read the output;",
                f"- write `{(rdir / 'REPORT.md').as_posix()}` (sections: Built, Verification evidence, Rulings, Needs "
                "your eyes, Proposals, Pending, Walkthrough) — the supervisor considers the run finished only when it exists;",
                "- update the bitácora (day log + walkthrough, PENDING, SUMMARY).", *ultra, "", "## Pointers",
                *_paths(project, rdir), "", "## Rules",
                "- Headless session: nobody answers questions. Decide, record a ruling, keep going. No `Aye`.",
                f"- Commit fixes on the feature branch `{branch}`; NEVER push, deploy or publish.",
                "- Use subagents for noisy work. Log this session in today's day log."]
        return "\n".join(head)
    out = [f"# Marathon {project} {req} — session {session}, task {task['id']}", "",
           f"Task **{task['id']}** — {task['title']}",
           f"- repo (role): {task['repo'] or '(workspace root)'}",
           f"- verify: {('`' + task['verify'] + '`') if task['verify'] else '(none machine-runnable; prove it yourself)'}",
           f"- depends on: {', '.join(task['after']) or 'nothing'} (already done)",
           f"- attempt {task['attempts'] + 1} of {state['limits']['max_attempts']}", *ultra, "", "## Pointers",
           *_paths(project, rdir)]
    bundle = _bundle(project, req)
    if bundle:
        out += ["", "## Context bundle", bundle]
    history = _recent_log(state, task["id"])
    if history or task.get("notes") or task.get("last_error"):
        out += ["", "## Previous attempts on this task"]
        out += history
        if task.get("last_error"):
            out.append(f"- last error: {task['last_error'][:600]}")
        out += [f"- note: {n}" for n in task.get("notes", [])]
        out.append("Do not repeat an approach that already failed; if the last error repeats, use `task fail --blocked`.")
    return "\n".join(out + [""] + _rules(project, req, task["id"], branch))


def agent_argv(state: dict, workdir: Path, prompt: str) -> tuple[list[str], str | None]:
    """(argv, stdin_text). Claude takes the prompt as the last argument; Codex reads it from stdin ('-')."""
    model = state.get("model")
    if state.get("agent") == "codex":
        exe = shutil.which("codex") or "codex"
        argv = [exe, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check",
                "-C", str(workdir)]
        if model and model != "haiku":
            argv += ["-m", model]
        return argv + ["-"], prompt
    exe = shutil.which("claude") or "claude"
    return [exe, "-p", "--model", model or "haiku", "--dangerously-skip-permissions", "--output-format", "json",
            prompt], None


def marathon_block() -> str:
    """SessionStart context for a marathon session (env BITACORA_RUN + BITACORA_TASK), '' otherwise."""
    req, task_id = os.environ.get("BITACORA_RUN"), os.environ.get("BITACORA_TASK")
    project = os.environ.get("BITACORA_PROJECT")
    if not (req and task_id and project):
        return ""
    try:
        rdir = find_req(ROOT / slugify(project, 60), req)
        state = rs.load(rdir) or {}
        task = rs.get_task(state, task_id)
    except (SystemExit, Exception):
        return ""
    cli = f'python "{SCRIPT.as_posix()}" --project {project}'
    if task_id == FINAL_TASK or task is None:
        return (f"### Current marathon task\n{req} FINAL session: fresh-eyes review, run the plan's Verification, write "
                f"`{(rdir / 'REPORT.md').as_posix()}`. No other work.")
    lines = [f"### Current marathon task (supervised run — re-read this after any compaction)",
             f"- {req} / **{task['id']}** — {task['title']}",
             f"- repo: {task['repo'] or '(workspace root)'} · verify: {task['verify'] or '(none)'} · "
             f"after: {', '.join(task['after']) or '-'}"]
    if task.get("last_error"):
        lines.append(f"- last error: {task['last_error'][:400]}")
    lines += [f"- note: {n}" for n in task.get("notes", [])]
    lines.append(f"Rule: work ONLY on this task; finish with `{cli} task done {req} {task['id']} --evidence \"...\"` "
                 f"or `task fail ... --reason \"...\"`.")
    return "\n".join(lines)
