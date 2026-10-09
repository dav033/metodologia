# Marathon mode

An external **supervisor** (`scripts/bt_run.py`) runs an approved PLAN for hours or days. It launches a **fresh
headless agent session per task**, keeps all state on disk, enforces the caps itself, detects stuck tasks, waits out
usage limits, survives reboots and notifies the user. Context never rots because every session starts clean; the
agent never has to "remember" anything — PLAN.md, RUN.json and the bitácora are the memory.

## Marathon vs loop

| | Loop / goal (`execution.md` §1c) | Marathon |
|---|---|---|
| Who drives | the agent itself, one long session | an external script, one session per task |
| Length | hours | days |
| Context | accumulates, needs `/clear` | clean for every task |
| Caps, stuck detection, usage-limit wait, reboot | none (manual) | built in |
| State | PLAN.md only | PLAN.md + `RUN.json` |

Default to marathon for plans with many tasks or that will outlast one sitting; keep the loop for a short plan you
expect to finish in a few hours.

## How it works

1. Plan approved (with **Modo: Maratón** on the web form, or via CLI). `launch --mode marathon` opens a Windows
   Terminal window titled `<project> <REQ> marathon` running the supervisor. The window stays visible: it prints one
   status line per session.
2. The supervisor creates/reads `RUN.json` (next to the spec, git-synced): task list parsed from PLAN.md, statuses,
   attempts, heartbeat, log of the last 200 sessions.
3. Loop: reload `RUN.json` (so controls are honored) → pick the next `todo` task whose `after:` dependencies are all
   done → build the session prompt → run ONE headless session with a hard timeout → classify the result → commit the
   bitácora → repeat.
4. When every task is done: a final session does the fresh-eyes review and writes `REPORT.md` (`execution.md` §4),
   then status `done`, PLAN `status: done`, notification, autostart removed.
5. If the only tasks left are blocked: status `blocked`, notification, exit.

The session output is saved machine-locally under `.state/runs/<project>-<REQ>/session-0007.log`.

### Task lines the supervisor parses

```
- [ ] T3 — <what> · repo: backend · after: T1, T2 · verify: `npm test -- orders` · covers: R1, US-2
```

`repo:`, `after:` and `verify:` are optional. `verify:` is run by the supervisor **only if it is inside backticks**
(from the task's repo dir, 10-minute timeout); free text is just guidance for the agent. Already-ticked `[x]` tasks
start as done. Write tasks small enough to finish in one session (minutes, not hours) and give each a machine-runnable
`verify` whenever possible: it is the supervisor's independent proof, the agent's claim alone is not trusted.

## What the session agent does (and must not do)

The session prompt carries the project/REQ/task (id, title, repo, verify), pointers (HANDOFF.md, SPEC.md, PLAN.md,
bitácora SUMMARY / ARCHITECTURE / TOOLS), a trace context bundle, the last log lines, notes and `last_error` for this
task, and the rules:

- Work **only on this task**. Follow `engineering.md` and run the antagonist gate before every commit.
- Commit on the feature branch. **Never push or deploy.**
- Finish with exactly one of:
  ```
  bitacora.py --project P task done REQ-001 T3 --evidence "<what proves it>"
  bitacora.py --project P task fail REQ-001 T3 --reason "<why>"
  ```
  `done` ticks the PLAN.md checkbox and appends to the Progress log. A note for the next attempt:
  `task note REQ-001 T3 --text "..."`.
- Log the session in the day log.

When `ultracode` is on (default) the prompt adds: *ultracode: use the Workflow tool for substantive multi-step work in
this task.*

## Caps, stuck tasks, usage limits

- **max_attempts** (default 3) per task, **session_timeout_min** (default 60) per session, **max_sessions** (default
  300) per run. Reaching max_sessions stops the run (status `stopped`) and notifies.
- **Failed attempt** = timeout, the agent called `task fail`, the agent exited without marking `done`, or `done` but
  the backticked `verify` failed (`verify_failed`; the task goes back to `todo`).
- **Stuck** = attempts >= max_attempts, or the same normalized error (`error_hash`: numbers, paths and hex stripped)
  twice. The task becomes `blocked`, a PENDING item is added
  (`P-0xx · [blocked] REQ T: title — reason · urgency: high · … · marathon`), `pending_id` is set, the user is
  notified, and the run **continues with other tasks** that do not depend on it.
- **Usage / rate limit** (output mentions usage limit, rate limit, 429, quota, "try again at"…): status `waiting`,
  `waiting_until` = now + backoff (30 min, doubling, max 4 h). It does **not** count as an attempt; one
  notification. The supervisor sleeps and retries by itself.

## Controls

| Action | Web (req tab **Maratón**) | CLI |
|---|---|---|
| Pause (after the current session) | Pausar | `bitacora.py --project P run-control REQ-001 pause` |
| Resume | Reanudar | `bitacora.py --project P run-control REQ-001 resume` |
| Stop | Detener | `bitacora.py --project P run-control REQ-001 stop` |

Controls write `control` into RUN.json; the supervisor polls it (paused: every 30 s). The tab also shows status,
progress x/y, current task, heartbeat age (a warning when older than session timeout + 10 min), `waiting_until`, the
task table and the last 30 log lines. The dashboard lists active marathons per project.

CLI to start by hand:

```
bitacora.py --project P run REQ-001 [--agent claude|codex] [--model haiku] [--no-ultracode]
    [--max-attempts 3] [--session-timeout 60] [--resume]
bitacora.py --project P launch REQ-001 --mode marathon --model haiku
```

`--agent-cmd "<template>"` (placeholders `{prompt_file} {workdir} {task} {req} {project}`) replaces the agent command;
it exists for tests only. `--once` runs a single session.

## Reboots and the stale heartbeat

On start the supervisor installs an autostart `.cmd` in the user's Startup folder
(`metodologia-run-<project>-<REQ>.cmd`) that reopens the terminal with `run <REQ> --resume`; it removes it when the run
ends as `done` or `stopped`. `--resume` continues from RUN.json and sends any `in_progress` task back to `todo`
(its session died with the machine). The heartbeat (`at`, `pid`, `machine`, `task`, `session`, `state`) is written
before and after every session: if it is stale the supervisor is dead — reopen it with `run REQ --resume`.

## Notifications

Windows toast ("Bitácora") on: blocked task, usage-limit wait, run done, run blocked, run stopped / cap reached.
Optional phone push through ntfy: create `.state/notify.json` with `{"ntfy_topic": "<secret-topic-name>"}` and
subscribe to that topic in the ntfy app. Notification failures never stop the run.

## Why Haiku 5.5 + ultracode

Marathon work is many small, well-specified tasks with an independent `verify`; a fast, cheap model burns far less of
the usage limit over days and the clean-session design removes its main weakness (long-context drift).
**ultracode** gives it the Workflow tool for the multi-step parts inside a task, and the verify + antagonist gate catch
its mistakes. A task that keeps failing is escalated by blocking it (and a PENDING item), not by silent retries; the
user can rerun a blocked task with a stronger `--model` after fixing the cause.

## Context care

- One task per session: the unit of work is sized so a clean session can finish it.
- On SessionStart (any source, especially after a compaction) the hook re-injects a **Current marathon task** block
  from `BITACORA_RUN` / `BITACORA_TASK`: REQ, task, verify, after, last_error, notes, and the rule *work only on this
  task; finish with task done/fail*.
- Noisy work (code sweeps, test suites, long logs) goes to subagents (`subagents.md`); the session keeps only
  conclusions.
- Notes for the next attempt go in `task note`, not in the agent's head: the next attempt is a different session.
