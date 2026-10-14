# REQ-008 T3 — Foreground lifecycle and T4 integration

## Implemented boundary

`bt_orchestration_terminal.run_child` starts a fresh direct child without setsid, in its
own process group within the supervisor's SID and controlling terminal. Foreground
ownership transfers to that group; bounded JSON stdin/stdout are protocol streams and
`/dev/tty` remains available. SIGCONT after transfer resumes an early SIGTTIN startup stop.
Input is limited before startup; aggregate output, deadline and stop are enforced while
running. Handlers and termios are restored on normal exit, interruption, timeout,
overflow and failed startup. The leader remains unreaped via waitid(WNOWAIT) until its
owned group is terminated, including surviving descendants; ownership is checked before
group signalling and PID/PGID reuse cannot occur during containment. The supervisor group
is never signalled. Its instance UUID is not proof of a provider conversation ID.

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

Continuation coordinator reran `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover
-s skill/scripts/tests -p test_orchestration_terminal.py -q`: 21 tests, OK, 4.329 seconds,
exit 0. Final bounded standards re-review approved the startup fix, group containment,
terminal restoration and reservation callers without concrete findings; it was static.

Final coordinator terminal suite: 21 tests, OK, 4.375 seconds, exit 0, after the SIGCONT
startup correction and fixture extraction (handoff evidence). Real PTYs check
controlling terminal/SID/foreground PGID, planner exit before successor, fresh process
and controlled provider conversation IDs, owned-group containment, early SIGTTIN,
direct SIGTERM, terminal SIGINT, timeout,
overflow and termios/handler restoration. A controlled runtime drives the real supervisor
through two dependent milestones and FINAL with T2 packages and task verification;
an assertion forbids every automatic commit call. Missing/stale/colliding parent cases
preserve the active client. No paid provider was invoked.

Before the final SIGCONT correction, combined focused regression passed 109/109 in
17.335 seconds (`/tmp/req008-t3-final-regressions.log`); package/install passed 10/10.
These checks were not rerun after that correction. The SIGTTIN regression was reproduced
red then green in `/tmp/req008-t3-sigttin-red.log` and `...-green.log`.

Earlier checks: marathon 27/27; relay 52/52; isolation/handoff/milestones/context-integrity
30/30 (3.421s, `/tmp/req008-t3-integration.log`); wheel/install 10/10 (3.182s,
`/tmp/req008-t3-package.log`). New modules/tests pass ruff; diff check and three CLI help
entries pass. Final scoped ruff passed with exit 0; closure must repeat diff check.
Broad legacy-file lint remains preexisting debt; full combined regression
belongs to the parent after M2. No separate typecheck configuration was found.

T4 now supplies `configured_runtime()` with pinned Claude structured reasoning and
deterministic admitted actions. Public foreground execution remains explicit opt-in and
preflights capability, authority and controlling TTY before opening/reserving a run.
An unavailable runtime still fails before effects; automatic replacement cannot target it.
No public test-provider flag, native fallback or production wait-only adapter was introduced.
The owner paused execution before final M2 acceptance/default activation; see REPORT.md.

T4 implements inventory/version/session-ID validation, structured actions, bounded receipts,
delegation/documentation/checkpoint/rotation and actual CLI proof through controlled PATH
fixtures. Foreground-child identity is persisted separately from worker session_pids, whose
orphan recovery assumes PGID=PID. Codex reasoning remains ineligible until proven;
Codex workers remain separate. Default activation is pending T4.
