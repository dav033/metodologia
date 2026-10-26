"""Bitácora hooks: SessionStart context, Stop gate, SessionEnd cleanup."""
from __future__ import annotations

from bt_core import *  # noqa: F403
from bt_views import *  # noqa: F403
from bt_core import _git, _load_bindings, _save_bindings
# ---------------------------------------------------------------- Stop gate

def _norm(p: str) -> str:
    return p.replace("\\", "/").lower()


def needs_logging(transcript: Path) -> tuple[bool, str]:
    """Look at the transcript since the last write into the bitácora."""
    # the bitácora is reachable through its link (~/bitacora) AND its real path (~/metodologia/bitacora)
    roots = {_norm(str(ROOT)), _norm(str(ROOT.resolve())), "~/bitacora"}
    events = []  # ("log" | "work" | "turn")
    try:
        with transcript.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("type") != "assistant":
                    continue
                content = (e.get("message") or {}).get("content") or []
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "text":
                        events.append("turn")
                    if c.get("type") != "tool_use":
                        continue
                    name, inp = c.get("name", ""), c.get("input") or {}
                    target = _norm(str(inp.get("file_path") or inp.get("notebook_path") or inp.get("command") or ""))
                    if any(r in target for r in roots) or "bitacora.py" in target:
                        if name in MUTATING_TOOLS or name in ("Bash", "PowerShell"):
                            events.append("log")
                        continue
                    if name in MUTATING_TOOLS:
                        events.append("work")
                    elif name in ("Bash", "PowerShell") and re.search(
                            r"git (commit|merge|push)|>>?\s*[\w./\\-]+\.\w+|\btee\b|sed -i|set-content|add-content"
                            r"|out-file|cat\s*>|<<\s*['\"]?\w+", target):
                        events.append("work")  # commits, and file writes done through the shell
    except Exception:
        return False, ""
    last_log = max((i for i, e in enumerate(events) if e == "log"), default=-1)
    tail = events[last_log + 1:]
    work = tail.count("work")
    turns = tail.count("turn")
    if work:
        return True, f"{work} file change(s)/commit(s) since the bitácora was last updated"
    if turns >= CHAT_TURNS_BEFORE_NUDGE:
        return True, f"{turns} replies since the bitácora was last updated"
    return False, ""


# ---------------------------------------------------------------- hooks

def _read_stdin_json() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def hook_start(harness: str = "claude") -> None:
    data = _read_stdin_json()
    sid = data.get("session_id", "")
    cwd = Path(data.get("cwd") or os.getcwd())
    source = data.get("source", "startup")
    from bt_vcs import pull
    sync_warning = pull(ROOT) if source in ("startup", "clear") and not _restricted_execution() else ""
    project = resolve_project(cwd, sid)
    top = _git(cwd, "rev-parse", "--show-toplevel")
    if project and top and not in_hq(cwd) and not ws.project_for_path(ROOT, top):
        register_repo(project, Path(top))
    ctx = build_context(project, sid, cwd, source)
    if sync_warning:
        ctx += f"\nWARNING: {sync_warning} — tell the user in one line."
    from bt_secrets import alert
    if alert(ROOT):
        ctx += ("\nWARNING: a possible SECRET was found in the bitácora and was NOT committed. Remove it (keep only a "
                "reference: key path, env var name, ssh alias), then run `bitacora.py commit \"fix: remove secret\"`. "
                f"Redacted report:\n{alert(ROOT)[:1500]}")
    if in_hq(cwd):
        from bt_server import ensure_server
        ctx += f"\nWeb UI (dashboard, rounds, plan approval): {ensure_server()}"
    from bt_orchestration_context import supervised_hook
    if harness == "codex" and supervised_hook(ROOT) is None:  # Legacy clients need full skill injection.
        ctx = skill_body() + "\n\n" + ctx
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))


def skill_body() -> str:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    return f"[metodologia skill — always active; references live in {SKILL_DIR.as_posix()}/references]\n" + body


def dirty_since_log(project: str, cwd: Path, day: Path) -> tuple[bool, str]:
    """Harness-agnostic fallback: files in the workspace repos changed after the day log was last written."""
    tops = [p for p in ws.repos(ROOT, project).values() if p.exists()]
    own = _git(cwd, "rev-parse", "--show-toplevel")
    if own and all(ws._key(own) != ws._key(t) for t in tops):
        tops.append(Path(own))
    last_log = day.stat().st_mtime if day.exists() else 0
    newer = 0
    for top in tops:
        for line in (_git(top, "status", "--porcelain") or "").splitlines():
            f = top / line[3:].strip().strip('"').split(" -> ")[-1]
            try:
                if f.is_file() and f.stat().st_mtime > last_log:
                    newer += 1
            except OSError:
                pass
    return (True, f"{newer} workspace file(s) changed since the bitácora was last updated") if newer else (False, "")


def hook_stop(harness: str = "claude") -> None:
    data = _read_stdin_json()
    from bt_secrets import alert
    if alert(ROOT) and not data.get("stop_hook_active"):
        print(json.dumps({"decision": "block", "reason": (
            "[bitácora] A possible secret was written into the bitácora and blocked from git. Find it (report: "
            f"{(ROOT / '.state' / 'secret-alert.txt').as_posix()}), replace the value with a reference (key path, env "
            "var name, ssh alias), then run `bitacora.py commit \"fix: remove secret\"`. If it's a false positive, add "
            "its fingerprint to bitacora/.gitleaksignore.")}))
        return
    sid = data.get("session_id", "")
    cwd = Path(data.get("cwd") or os.getcwd())
    project = resolve_project(cwd, sid)
    tp = data.get("transcript_path")
    if not project and tp and sid:  # e.g. a session in the home folder: bind by the repos it touched
        touched = ws.projects_in_transcript(ROOT, Path(tp))
        if len(touched) == 1:
            project = touched.pop()
            bindings = _load_bindings()
            bindings[sid] = project
            _save_bindings(bindings)
            pdir, _ = ensure_project(project)
            ensure_session_block(pdir, sid, cwd)
    if not project:
        return
    from bt_continuation import save_checkpoint
    save_checkpoint(ROOT, project, sid)
    try:  # planning-time Designer and translation follow the conversation even with no web page open
        import bt_design_drafts
        bt_design_drafts.follow_project(ROOT, project)
    except Exception:  # noqa: BLE001, S110 - the hook must never trap a session on its own error
        pass
    try:
        import bt_plan_gate
        held = bt_plan_gate.hold_reason(ROOT, project, sid)
    except Exception:                       # the gate must never trap a session on its own error
        held = None
    if held:
        print(json.dumps({"decision": "block", "reason": held}))
        return
    if data.get("stop_hook_active"):
        return
    day = day_paths(ROOT / project, today())["day"]
    if harness == "codex" or not tp:  # Codex transcript format isn't a stable interface: use git instead
        need, why = dirty_since_log(project, cwd, day)
    else:
        need, why = needs_logging(Path(tp))
    if not need:
        return
    reason = (f"[bitácora] {why}. Before stopping, update your session section (`{sid[:8]}`) in "
              f"`{day.as_posix()}` (Done / Decisions / Not done / Pending / Next), and propagate new decisions "
              f"and pending items to DECISIONS.md / PENDING.md (and SUMMARY.md if the state changed). "
              f"Keep it short; if truly nothing worth logging happened, add one line saying so.")
    print(json.dumps({"decision": "block", "reason": reason}))


def hook_end() -> None:
    data = _read_stdin_json()
    sid = data.get("session_id", "")
    try:
        import bt_presence
        bt_presence.record(ROOT, {**data, "hook_event_name": "SessionEnd"}, None)
    except Exception:
        pass
    cwd = Path(data.get("cwd") or os.getcwd())
    project = resolve_project(cwd, sid)
    if not project:
        return
    from bt_continuation import save_checkpoint
    save_checkpoint(ROOT, project, sid)
    try:  # planning-time Designer and translation follow the conversation even with no web page open
        import bt_design_drafts
        bt_design_drafts.follow_project(ROOT, project)
    except Exception:  # noqa: BLE001, S110 - the hook must never trap a session on its own error
        pass
    pdir = ROOT / project
    day = day_paths(pdir, today())["day"]
    if day.exists() and sid and not _restricted_execution():
        text = day.read_text(encoding="utf-8")
        tag = f"`{sid[:8]}`"
        # drop a session block that was never filled in (still identical to the template)
        empty_block = re.compile(r"\n---\n\n## Session [^\n]*" + re.escape(tag) + r"[^\n]*\n\n"
                                 + re.escape(render("SESSION.md")))
        new = empty_block.sub("", text)
        if new == text and tag in text:
            new = text.rstrip("\n") + f"\n\n_Session `{sid[:8]}` ended {dt.datetime.now():%H:%M}._\n"
        if new != text:
            if new.strip() == text.splitlines()[0].strip():  # only the "# date — project" header is left
                day.unlink()
            else:
                day.write_text(new, encoding="utf-8")
    import bt_pending
    bt_pending.sort_file(pdir)
    write_index(pdir)
    write_global_index()
    from bt_vcs import commit
    if not _restricted_execution():
        commit(ROOT, f"{project}: session {sid[:8]} end")


def _restricted_execution() -> bool:
    return bool(os.environ.get('BITACORA_EXECUTION_POLICY'))


