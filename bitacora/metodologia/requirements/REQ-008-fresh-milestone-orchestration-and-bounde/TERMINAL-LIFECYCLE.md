# REQ-008 T3 — Foreground lifecycle and T4 integration

## Implemented boundary

`bt_orchestration_terminal.run_child` starts a fresh direct child without setsid or a
new process group. Child and supervisor share the controlling terminal and foreground
group; bounded JSON stdin/stdout are protocol streams and `/dev/tty` remains available.
Input is limited before startup; aggregate output, deadline and stop are enforced while
running. Handlers and termios are restored on normal exit, interruption, timeout,
overflow and failed startup. Only the unreaped direct Popen child is signalled; never
the shared process group. Its instance UUID is not proof of a provider conversation ID.

`ForegroundRuntime` version 1 supplies `check_capabilities`, `session_route` and
`run_session` to the existing supervisor. Routing precedes attempt/session reservation;
dependency selection, independent task verification and settlement stay authoritative.
Foreground execution is serial and disables autostart and automatic bitácora commits.
Persisted `orchestration_mode: foreground-v1` prevents silent native-mode resume.
Missing authority or an old RUN without context_run_id cannot enter bounded execution.
Entry moved to `bt_runentry` to keep bt_run below 500 lines; legacy worker groups stay separate.

## Planning transition

Explicit public entries are `handoff REQ-NNN --foreground --planning-session SESSION`,
`launch REQ-NNN --foreground --planning-session SESSION`, and manual
`run REQ-NNN --foreground --no-autostart`, through checkout `skill/scripts/bitacora.py`.
The manual result contains the absolute checkout command and active BITACORA_ROOT.
Missing/stale parent proof never signals a client or types into its terminal. Existing
prepared successors are preserved. Forced approval, new-repo setup and detached
supervisor launch cannot be combined with this entry.

With a compatible parent and activated runtime, capability preflight precedes spawning
a detached helper. Its private schema-1 request is size/owner/mode checked. The helper
rechecks authority/capabilities and reuses `run_wrapper`: wait for a turn-ended marker
newer than the request, reverify PID/start/direct-parent proof, claim once, write the
successor and end only the verified planner. The relay parent reaps the planner before
starting the supervisor. There is no multiplexer fallback. Only the helper is detached.

## Evidence and remaining T4 work

Terminal suite: 14 tests, OK, 1.775 seconds, `/tmp/req008-t3-terminal.log`. Real PTYs check
controlling terminal/SID/foreground PGID, planner exit before successor, fresh process
and controlled provider conversation IDs, direct SIGTERM, terminal SIGINT, timeout,
overflow and termios/handler restoration. A controlled runtime drives the real supervisor
through two dependent milestones and FINAL with T2 packages and task verification;
an assertion forbids every automatic commit call. Missing/stale/colliding parent cases
preserve the active client. No paid provider was invoked.

Other checks: marathon 27/27; relay 52/52; isolation/handoff/milestones/context-integrity
30/30 (3.421s, `/tmp/req008-t3-integration.log`); wheel/install 10/10 (3.182s,
`/tmp/req008-t3-package.log`). New modules/tests pass ruff; diff check and three CLI help
entries pass. Broad legacy-file lint remains preexisting debt; full combined regression
belongs to the parent after M2. No separate typecheck configuration was found.

T4 must implement `configured_runtime()` with verified Claude structured reasoning and
deterministic admitted actions. Until then public foreground execution reports
FOREGROUND_RUNTIME_NOT_ACTIVATED before opening/reserving a run; automatic replacement
cannot target an unavailable runtime. No public test-provider flag, native fallback or
production wait-only adapter was introduced. T3 is lifecycle evidence, not completion of M2.

T4 owns inventory/version/session-ID validation, structured actions, bounded receipts,
delegation/documentation/checkpoint/rotation and actual CLI proof through controlled PATH
fixtures. Persist foreground-child identity separately from worker session_pids, whose
orphan recovery assumes PGID=PID. Codex reasoning remains ineligible until proven;
Codex workers remain separate. Default activation is pending T4.
