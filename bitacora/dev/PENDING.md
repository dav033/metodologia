# dev — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-006 · [closed 2026-10-19 by session 71481911: owner asked to free ≥100 GB; Baldur's Gate 3 install (146 GB) + two /home snapper timeline snapshots holding it + pacman/yay/npm caches removed; `/` 244 GiB → 97 GiB used (21 %)] Disk `/` (btrfs) was at 97 % · urgency: high · complexity: S · added 2026-10-19 · D-008
- P-129 · Baldur's Gate 3 install (146 GB) deleted by mistake during the disk cleanup (owner wanted only installer files, which another session had already removed at the owner's request at 10:41: `~/Downloads/dtest` ISO + rar parts, 218 GB, and 8 /home snapshots). Neither installer nor install remains; saves kept. Decide: reinstall from its source, or best-effort `btrfs restore` from a live USB to an external disk (>150 GB) before more writes reuse the freed blocks · urgency: high · complexity: S · added 2026-10-19 · session 71481911
- P-012 · [closed 2026-10-19 by D-016: `scheduler-watch` restarts a dead owner with backoff and a failure budget] · urgency: high · complexity: M
- P-001 · Remove the marathon (relocate shared bt_run* helpers, scheduler as the only launch/handoff path, delete modules/tests/docs) · urgency: high · complexity: L · added 2026-10-18 · session 8c9cf122
  C2 relay completed in session 01a151b0: retired tests migrated, shared coverage retained and Scheduler launch regressions fixed. C3 documentation and overall acceptance reconciliation remain; see the day log for targeted checks and the pre-existing collection failure.
- P-007 · [closed 2026-10-19 by D-018: the execution port answers PortNotReady until the executor exists] · urgency: med · complexity: S
- P-128 · pictures/REQ-019's M4 store keeps ~83 k old `stream_gap` rows and ~48 k info incidents (224 MiB, M1 audit has the same incidents): decide on compaction/retention (destructive, owner's call). The running `scheduler-run` (started 10:29) still uses the old stderr rule for `unsupported_event` (~200 rows/h) until its next restart · urgency: med · complexity: S · added 2026-10-19 · D-017
- P-008 · Oracles written by the agent that builds the feature (the phone audit by T4) can be weaker than the criteria they verify; the verifier only reads exit codes. Consider a reviewer step that compares each check's assertions with its criterion, and an end-to-end smoke test of the verifier with a minimal JS repo · urgency: med · complexity: M · added 2026-10-19 · D-010 · partly done 2026-10-19: verifier smoke test exists (D-016); still open: reviewer step for oracle strength, whole-run smoke with a fake agent
- P-009 · Distribution across accounts is still uneven: 22 of 32 REQ-019 attempts ran on `codex-luis` (lowest pressure, 17 %). The load penalty (4 points per session in 5 h, cap 40) does not rebalance a gap that size; consider a share cap per account per plan or a stronger penalty · urgency: med · complexity: M · added 2026-10-19 · D-002
- P-011 · Cancelled attempts leave `running` rows in the executor ledger; executor roots and one worktree with `node_modules` per attempt are never cleaned (about 1 GiB per hour; the disk is no longer critical after P-006) · urgency: med · complexity: M · added 2026-10-19 · D-008
- P-013 · [closed 2026-10-19 by D-016: `scheduler-op` cancel-attempt, reopen, revise, stop, resume, status] · urgency: med · complexity: M
- P-130 · Owner of pictures/REQ-019 died with SIGBUS at 13:11 inside SQLite (M6 `store.py` `_transaction`, called from `process_reserved`) with the disk NOT full (352 GiB unallocated): the cause is unknown (a truncated/deleted mmap'd store file?). The new watchdog resumed it in seconds (first real catch). It happened again at 13:26 (exit -7, ~15 min later, in `queued_requests` of the dispatcher thread); the watchdog resumed it again. Lead, unproven: other processes read the same store (`bt_flow_bus._ro`, `mode=ro`, from the /flow work of another session) while the owner holds it in WAL mode. Trace in `~/.local/tmp/claude-1000/req019-run.log` and `~/bitacora/.state/watch/pictures-REQ-019.log` · urgency: med · complexity: M · added 2026-10-19 · D-016
- P-131 · Decision requests are only on the CLI and the watchdog notification: show them in the /flow panel and send them to Telegram with buttons (REQ-027 T14); add the «other route or account» option once the route pin exists · urgency: med · complexity: M · added 2026-10-19 · D-020
- P-132 · Prerequisites that a plan knows in advance (a Telegram token, an OAuth App) need a `needs` field in PLAN.json: ask in one batch before launch instead of blocking at the task that uses them · urgency: med · complexity: M · added 2026-10-19 · D-020
- P-133 · Skippable decision requests get no timeout yet: after a long wait (about 12 h) apply the recommendation when it is only a retry, and record that it was by timeout; unskippable ones never · urgency: med · complexity: M · added 2026-10-19 · D-020
- P-003 · [closed 2026-10-19 by D-005: M6 sandbox mounts Node, Playwright, the attempt's node_modules and git metadata read-only] · urgency: med · complexity: ?
- P-004 · [closed 2026-10-19 by D-006: REQ-019 plan revision 2 has no manual checks] · urgency: med · complexity: ?
- P-005 · `test_audit_routing.py` has 3 failures from before D-002 (audit tier escalation vs the role policy) · urgency: low · complexity: S · added 2026-10-19 · session 8eef50ee
- P-002 · [closed 2026-10-19 by SUPERRR H1: `bt_attempt_facts` shows each attempt's own route, tokens and model_reported from M2/M4; cost still not reported by providers] Show per-attempt model/account for earlier scheduler attempts and read model_reported/cost from the executor ledger · urgency: low · complexity: M · added 2026-10-18 · session 8c9cf122
- P-010 · The publication step is detected from the verification text (`git merge-base --is-ancestor HEAD origin/main`), not from a declared field of PLAN.json; the planner contract has no way to say "this task publishes" · urgency: low · complexity: M · added 2026-10-19 · D-013

## Blocked
_None_

## Recently closed
_None_
