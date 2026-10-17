# Marathon mode

An external **supervisor** (`scripts/bt_run.py`) runs an approved PLAN for hours or days. It launches a **fresh
headless agent session per task** (per milestone when the plan groups tasks under `### Mn` headings), keeps all state on disk, enforces the caps itself, detects stuck tasks, waits out
usage limits, survives reboots and notifies the user. Context never rots because every session starts clean; the
agent never has to "remember" anything — PLAN.md, RUN.json and the bitácora are the memory.

For a user asking for overnight or multi-day autonomous development, explain this mode and its resume/pause controls
before choosing it. Use [`agent-orchestration.md`](agent-orchestration.md) to decide task dependencies, worker
ownership, and verification. Marathon is a bounded execution mechanism: it does not authorize external or destructive
actions, permission bypass changes, or skipping the existing plan approval gate.

## Marathon vs loop

| | Loop / goal (`execution.md` §1c) | Marathon |
|---|---|---|
| Who drives | the agent itself, one long session | an external script, one session per task or milestone |
| Length | hours | days |
| Context | accumulates, needs `/clear` | clean for every task |
| Caps, stuck detection, usage-limit wait, reboot | none (manual) | built in |
| State | PLAN.md only | PLAN.md + `RUN.json` |

Default to marathon for plans with many tasks or that will outlast one sitting; keep the loop for a short plan you
expect to finish in a few hours. The decision also depends on whether each task can be expressed as a small,
independently verifiable unit; break down oversized tasks before launching.

## How it works

1. Plan approved (with **Modo: Maratón** on the web form, or via CLI). `launch --mode marathon` opens a native
   terminal window running the supervisor (Linux, macOS or Windows). The window stays visible: it prints one
   status line per session.
2. The supervisor creates/reads `RUN.json` (next to the spec, git-synced): task list parsed from PLAN.md, statuses,
   attempts, heartbeat, log of the last 200 sessions.
3. Loop: reload `RUN.json` (so controls are honored) → pick the next `todo` task whose `after:` dependencies are all
   done → build the session prompt → run ONE headless session with a hard timeout → classify the result → commit the
   bitácora → repeat.
4. When every task is done: a final session does the fresh-eyes review and writes `REPORT.md` (`execution.md` §4),
   then status `done`, PLAN `status: done`, notification, autostart removed.
5. If the only tasks left are blocked: status `blocked`, notification, exit.

The coordinator's plan remains the source of truth for scope and dependencies. The current supervisor dispatches one
task session at a time in dependency order. Parallelism within a task is appropriate only when the harness supports
it and ownership is disjoint. Each task session must return its status and evidence, while the supervisor's
verification decides whether `done` is accepted.

**Live session logs.** The agent writes straight into `.state/runs/<project>-<REQ>/session-0007.log` (machine-local)
while it runs, so `tail -f` shows it live and a killed or timed-out session still leaves its transcript. Claude runs
with `--output-format stream-json --verbose`: one JSON event per line (turns, tool calls, tool results) and a final
`result` event whose `is_error`, `result` and `total_cost_usd` the supervisor reads (the cost goes into the log
entry). Usage-limit detection reads that `result` event; when it never came, only the non-JSON lines (stderr) count,
so tool output in the transcript is never mistaken for a limit. Logs are capped at the last ~1 MB.

**Early termination.** `claude -p` can stay alive long after the agent finished (background jobs), and run into the
session timeout. While a session runs the supervisor polls RUN.json; once the agent has given its verdict for the
current task (`task done`, `task fail`, `task escalate`; for the final session, a fresh REPORT.md) it waits a 90 s
grace period (`BITACORA_RUN_GRACE_SEC` overrides it, for tests), then kills the session's process tree and settles
normally (verify, tick, log with `early_exit`; a `task fail` keeps the agent's reason, not "timeout"). If the agent
takes its verdict back (done, then fail) the grace starts over. Hence the prompt rule: the verdict is the **last**
command, after the day log and every commit, and nothing may be left running in the background.

### Task lines the supervisor parses

```
- [ ] T3 — <what> · repo: backend · after: T1, T2 · verify: `npm test -- orders` · covers: R1, US-2
- [ ] T4 — <design the sync protocol> · level: architecture · verify: `pytest tests/sync`
```

`repo:`, `after:`, `verify:`, `level:`, `kind:` (implement, test, docs, audit, research; inferred from the title when
absent), `complexity:` (S, M, L: recorded in telemetry so agents can be compared on comparable work) and `risk:`
(`high` makes the automatic hand-off ask for approval) are optional. `level: architecture` marks a hard architecture/design task:
it starts at the top of the escalation ladder (opus, effort high) instead of haiku. `verify:` is run by the supervisor **only if it is inside backticks**
(from the task's repo dir, 10-minute timeout); free text is just guidance for the agent. Already-ticked `[x]` tasks
start as done. `repo`, `after`, `verify` and `level` are **frozen when the run starts**: later edits to PLAN.md (even by the
agent) are reported as plan drift and not adopted, so a session cannot rewrite its own gate; to change them, edit
RUN.json. New task lines are added. Write tasks small enough to finish in one session (minutes, not hours) and give each a machine-runnable
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
  `done` records the claim in RUN.json; the supervisor ticks the PLAN.md checkbox (and appends to the Progress log) only
  after its own `verify` passes. The session can only mark **its own task** (`task done|fail|note` for another id is
  rejected). `task fail REQ T --reason "..." --blocked` blocks the task at once. A note for the next attempt:
  `task note REQ-001 T3 --text "..."`.
- If the task turns out to be a hard architecture/design problem, or it can't find a solution, it does not flail:
  `task escalate REQ-001 T3 --to opus --reason "..."` (architecture) or `--to sonnet` (stuck), then stops (see
  the escalation ladder below).
- Wait for every workflow/subagent/background job it started before `task done`; leave nothing running.
- Log the session in the day log **before** the verdict: `task done|fail|escalate` is the last command (the
  supervisor ends the session shortly after it).

When `ultracode` is on (default) the prompt adds: *ultracode: use the Workflow tool for substantive multi-step work in
this task.*

## Caps, stuck tasks, usage limits

- **max_attempts** (default 4: haiku, sonnet, opus, opus) per task, **session_timeout_min** (default 60) per
  session, **max_sessions** (default 300) per run. Reaching max_sessions stops the run (status `stopped`) and
  notifies. A RUN.json created before the default changed keeps its own value.
- **Failed attempt** = timeout, the agent called `task fail`, the agent exited without marking `done`, or `done` but
  the backticked `verify` failed (`verify_failed`; the task goes back to `todo`). Every failed attempt moves the task
  **one tier up** the escalation ladder for its next session.
- **Escalated session** = the agent called `task escalate`: it counts toward max_attempts but is not a failure (no
  `error_hash`, never "same error twice").
- **Stuck** = attempts >= max_attempts, or the same normalized error (`error_hash`: numbers, paths and hex stripped)
  twice **with the second one already at the top tier** (opus); a repeated error below the top just escalates. The
  task becomes `blocked`, a PENDING item is added
  (`P-0xx · [blocked] REQ T: title — reason · urgency: high · … · marathon`), `pending_id` is set, the user is
  notified, and the run **continues with other tasks** that do not depend on it.
- **Usage / rate limit** (a **failed** session — non-zero exit or `is_error` — whose output mentions usage limit,
  rate limit, 429, quota, "try again at"…; a successful run that merely mentions them is not a limit): status
  `waiting`, `waiting_until` = now + backoff (30 min, doubling, max 4 h). It does **not** count as an attempt; one
  notification. The supervisor sleeps and retries by itself. After 8 limit results in a row on the same task, the
  next one is logged as `limit_streak`: it is **not an attempt and never a failure** (no `error_hash`, no "same
  error twice", no tier climb, `attempts` untouched), so limits alone never block a task or use up the ladder. It
  is counted in the task's `limit_streaks`, the supervisor waits after it like after any limit, and the user is
  notified on every streak (a misread failure that keeps looking like a limit can only be told apart by a human;
  `max_sessions` bounds it).
- **Done is a claim until verified.** Under the supervisor `task done` only sets `claimed_done` on the task (status
  stays `in_progress`); the task becomes `done`, and the PLAN.md box is ticked, once the supervisor's own `verify`
  passes. If the supervisor dies in between, the next start (`--resume`, autostart) re-runs the `verify` of every
  claimed-but-unverified task **before** picking new work (a failed verify is a normal failed attempt). A RUN.json
  from before this change, with a bare `done`, is trusted as it was.
- **Checkpoint is a resume hint, not fresh evidence.** On resume, load the approved plan and RUN.json, inspect the
  worktree and logs, and re-run each claimed task's verification before scheduling new work. Re-check any external
  fact, approval or environment assumption that may have changed since the checkpoint; never infer that a checkpoint
  authorizes an external side effect.
- **Supervisor errors** (RUN.json locked by git/antivirus, a missing file…) are logged, notified once, retried with a
  growing pause and only given up on after 10 in a row. A missing agent executable stops the run and notifies.

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
    [--max-attempts 4] [--session-timeout 60] [--resume]
bitacora.py --project P launch REQ-001 --mode marathon --model haiku
```

`--agent-cmd "<template>"` (placeholders `{prompt_file} {workdir} {task} {req} {project} {model_args}`, the last one
being the tier's `--model … --effort …`) replaces the agent command;
it exists for tests only. `--once` runs a single session. `--retry-blocked` puts blocked tasks back to `todo` with
fresh attempts (use it after fixing the cause listed in PENDING.md). `--no-autostart` skips the per-user login entry.
`--resume` is accepted for readability but implicit: the supervisor always continues from RUN.json if it exists.
Codex receives its prompt on stdin (`exec ... -`) instead of as an argument; Claude takes it as the last argument.

## Remote monitoring (Remote Control)

The simplest way to follow a run from a phone is the conversation that launched it: `/rc` on that session, which
keeps `bitacora.py watch REQ-NNN` armed in the background and tells each milestone as it closes
(`requirements.md` §8). The executor sessions are separate headless processes: they never appear inside that
conversation and ending them does not touch it. The companion session below is the alternative for a run that was
launched from the web panel or from a terminal nobody is attached to.

Task sessions are headless, and Remote Control only attaches to interactive sessions — so a marathon launched with
Claude also opens a **monitor**: an interactive Haiku session named "`<project> <REQ> maratón`", started with
`claude --remote-control`, briefed by `MONITOR.md` (written next to the plan). The user opens it from claude.ai/code or
the Claude app and asks "¿cómo va?", "¿por qué se bloqueó T4?", "muéstrame el último commit", or "pausa / reanuda /
detén". The monitor reads RUN.json, the session logs, git and PENDING, and steers only through `run-control` and
`task note`; it never edits code. It is independent of the supervisor (closing it never stops the run) and idle
until asked.
- Open it again any time: `bitacora.py --project P monitor REQ-001`, or the web tab's **Abrir monitor remoto**.
- To start HQ sessions from the phone too, run `claude remote-control --name HQ` inside `~/bitacora`.

## Reboots and the stale heartbeat

On start the supervisor installs a per-user login entry that runs `run <REQ> --resume`:
Windows Startup `.cmd`, Linux systemd user service (XDG `.desktop` when systemd is absent), or
macOS `~/Library/LaunchAgents/*.plist`. POSIX entries resume headlessly; inspect RUN.json, logs or the web UI.
Entries take effect at the next login and are removed when the run ends as `done` or `stopped`.
The generated scripts preserve `BITACORA_ROOT` and the launch PATH. A Linux session without a user
systemd manager must support XDG Autostart or resume manually; errors are reported, not hidden. A restart continues from RUN.json, sends any
`in_progress` task back to `todo` (its session died with the machine), and **keeps an explicit pause and a pending
usage-limit wait** (only `run-control resume` lifts a pause). The heartbeat (`at`, `pid`, `machine`, `task`, `session`, `state`) is written
before and after every session: if it is stale the supervisor is dead — reopen it with `run REQ --resume`.

## Notifications

Native notifications (Windows toast, Linux notify-send, macOS osascript) on: blocked task, usage-limit wait, run done, run blocked, run stopped / cap reached.
Optional phone push through ntfy: create `.state/notify.json` with `{"ntfy_topic": "<secret-topic-name>"}` and
subscribe to that topic in the ntfy app. Notification failures are reported to stderr and never stop the run.

## Why Haiku 5.5 + ultracode

Marathon work is many small, well-specified tasks with an independent `verify`; a fast, cheap model burns far less of
the usage limit over days and the clean-session design removes its main weakness (long-context drift).
**ultracode** gives it the Workflow tool for the multi-step parts inside a task, and the verify + antagonist gate catch
its mistakes. A task that Haiku cannot finish climbs the escalation ladder instead of being retried blindly; only a
task that also fails at the top is blocked (with a PENDING item).

## Escalation ladder

The ladder below governs implementation. Audits have a separate budget (`agents.md`): Sonnet 5.5 medium normally,
Opus 5.5 high for high-risk/architecture milestones or escalation, Sol medium fallback (high on escalation).
This also applies when pinned to a provider; audits never inherit the builder's model or default xhigh/max.

Tiers are capability levels shared by every provider. With an account pool (`run --pool auto`, the default of
`handoff`) each session's account, model and effort come from the router, and a failed attempt climbs one tier
**and** prefers another provider: `agents.md` has the full table (Claude: haiku → sonnet medium → opus high; Codex:
gpt-6-luna medium → gpt-6.1-sol medium → gpt-6.1-sol high). The table below is a run pinned to one agent.

| Tier | Claude | Codex |
|---|---|---|
| 0 | the run's `--model` (default **haiku**), default effort | its model, default effort |
| 1 | **sonnet** `--effort medium` | same model, `-c model_reasoning_effort="medium"` |
| 2 (top) | **opus** `--effort high` | same model, `-c model_reasoning_effort="high"` |

A configured model already stronger than a tier's (e.g. `--model opus`) is kept; only the effort follows the tier. Codex never
switches model: from tier 1 up it only raises the reasoning effort. Nothing climbs to `xhigh` by itself: a task that
justifies it says so on its PLAN line (`effort: xhigh`), and the route records that explicit choice.

- Each task keeps its `tier` (0–2) in RUN.json; each log entry records the `model` and `effort` of that session
  (the web tab shows both: the task table's **Modelo** column and the log's).
- **Up one tier** after every failed attempt (`failed`, `verify_failed`, `timeout`), capped at opus. A usage limit
  or a user stop does not move it.
- **Same error twice** below the top → escalate; at the top (opus) → `blocked`. With the default max_attempts 4 a
  task gets haiku, sonnet, opus, opus.
- **Start tier** (`bt_routing_policy.start_tier`, a floor and never a ceiling; the reason is stored as `tier_reason`):
  docs, test, research and implement start at 0; `complexity: L` or `risk: high` start at 1 (2 for an implementation
  with both); `level: architecture` starts at tier 2 whatever the kind; audits start at 1.
- **Session grouping.** A milestone session takes only pending tasks that share the first one's tier, kind and risk
  class, up to `limits.group_max` per tier (default tier 0: 3, tiers 1–2: 1; also `routing.group_max`), in plan order
  and with dependencies inside the group or already done. A hard task never lifts its light neighbours.
- **Timeouts.** New runs bound a task session by tier (`session_timeout_by_tier`: 25 / 45 / 60 min), capped by
  `session_timeout_min`; a session carrying several tasks gets up to three times that. An explicit `--timeout`
  replaces the table; runs started before it keep their stored value. Claude Code 2.1.302 has no turn limit flag
  (`--max-turns` does not exist; `--max-budget-usd` is API-only), so the timeout and the stagnation rule are the bounds.
- **Stagnation.** A failed attempt whose resulting working tree equals the previous attempt's counts as idle; after two
  idle attempts in a row the task is blocked with that diagnosis (a repeated error still blocks at the top tier).
- **`task escalate REQ T --to standard|top --reason "..."`** (aliases `sonnet`, `opus`) (only for the session's own task) raises the tier, stores
  the reason in the task's notes so the next session reads it, and marks the session `escalated`. A target at or
  below the current tier is refused (the agent uses `task fail` instead), so an opus session cannot burn attempts
  "escalating" in place. Run by hand (no supervisor), it only changes the tier.
- `--retry-blocked` puts the task back at its starting tier (0, or 2 for `level: architecture`).
- The final review session climbs the same ladder with each failed attempt.

## Context care

- One task per session: the unit of work is sized so a clean session can finish it.
- On SessionStart (any source, especially after a compaction) the hook re-injects a **Current marathon task** block
  from `BITACORA_RUN` / `BITACORA_TASK`: REQ, task, verify, after, last_error, notes, and the rule *work only on this
  task; finish with task done/fail*.
- Noisy work (code sweeps, test suites, long logs) goes to subagents (`subagents.md`); the session keeps only
  conclusions.
- Notes for the next attempt go in `task note`, not in the agent's head: the next attempt is a different session.

## Milestone sessions and audits

A plan with `### M1 — title` headings runs one fresh session per **milestone** instead of per task: the session gets
every pending task of the milestone (`BITACORA_TASK=T1,T2,T3`), gives each its own verdict, and the supervisor settles
and verifies each task separately. A task not reached because a task it depends on failed is `skipped` without
counting an attempt; a session that times out gets up to three task timeouts. With a pool, a synthetic task
`M1-audit` follows each milestone: an independent agent audits and may fix, and its verification is every verify
command of the milestone again. The auditor closes with `task done ... --findings N --severity high=N,med=N,low=N`
(0 when clean; omitted = unknown, never 0): that count feeds the quality metrics in `agents.md`. Details and switches: `agents.md`. Plans without those headings are unchanged.

## Concurrent sessions (`run --workers 2`)

Same-repository parallel sessions are opt-in: `run REQ-NNN --isolation worktree --workers 3`. Each eligible unit
gets its own branch/worktree; same-repo units run together only when every task declares disjoint `files:` scopes
and no `resources:` tag is shared. Units without `files:` stay serial. Candidates merge one at a time into a durable
`wt/REQ-NNN-integration-*` branch and pass their combined verify commands before the RUN task is marked done.
The default `run.isolation` config is `off`; `run --isolation off` selects the legacy scheduler explicitly.

Opt-in; the default is one session at a time and behaves exactly as before. With `--workers 2` the supervisor runs
two tasks at once **only when it is provably safe**: both name a `repo:` role, the roles differ, their dependencies
are done and no task of that repo is in progress. A task without `repo:` (workspace root) may touch anything, so it
always runs alone; two tasks of one repository never overlap. The cap is 2 until the machine's behaviour under several
agent sessions is measured. Same-repository parallelism would need per-task worktrees and a serialized merge policy
and is not implemented.

Shared bitácora files (PLAN.md ticks, PENDING.md items, the bitácora's git index) are written under `bt_lock`
critical sections, so concurrent sessions queue instead of interleaving. Each running session's pid is tracked, and a
resume after a supervisor crash ends every orphaned session before starting new ones. Plan tasks that should be
parallelizable must declare their repo role: `- [ ] T4 — … · repo: backend`.
