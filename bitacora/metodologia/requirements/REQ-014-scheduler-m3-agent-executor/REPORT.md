# REQ-014 — Scheduler M3 Agent Executor — final report (2026-10-14)

## What was built
- `skill/scripts/bt_scheduler_executor/` (stdlib only, isolated, own README): ledger (SQLite WAL, unique ids/keys, checked state machine, write-ahead event outbox), `GitWorkspaces` (worktree + branch per attempt, per-repo lock, journal, idempotent), recoverable **handoff** (committed + uncommitted + untracked as a snapshot commit under `refs/m3/*`, binary patch, manifest, continuation brief; branch/index/base untouched), detached double-forked **shim** (timeout, capped output, `exit.json`), supervisor (`start`/`cancel`/`query`, heartbeats, events), cause classification, restart reconciliation, CLI (`status|show|events|selftest`).
- `skill/scripts/bt_scheduler_executor_adapter.py`: the only importer. Route validation against `bt_agents`/`bt_profiles` (provider↔model, effort per provider, profile policy, work-only gate on the project's repository before any side effect), launch/classification through `bt_driver`, account environment boundary (+ parent-session state and foreign credentials dropped), brief from the frozen plan, translation to the core's `Ack`/`ExecutionStatus`/`Event`, `wire()` opt-in entry, `worktree_allocation` for `bt_worktree`.
- Docs: module README (ports, life cycle, causes, events, limits, acceptance table), `references/modules.md` section, `pyproject.toml` entries, wheel test; D-024, P-027.
- SPEC/PLAN/PLAN.json r1 were authored here: the goal presupposed approved M3 documents that did not exist.

## Evidence (all run 2026-10-14 after the last change)
| Command | Result |
|---|---|
| `cd skill/scripts && python -I -W error::ResourceWarning -m unittest discover -s bt_scheduler_executor/tests` | 243 OK (incl. lone-copy isolation, 11 crash-at-every-step, concurrency, cancel/reconcile/classification matrices, hardening regressions) |
| `python -W error::ResourceWarning -m unittest tests.test_scheduler_executor_adapter tests.test_scheduler_executor_integration tests.test_scheduler_integration tests.test_plan_integration` | 132 OK (real `SchedulerCore` + executor + fake provider binaries; boundaries from outside; historical RUN.json byte-identical) |
| `unittest discover -s bt_scheduler_core/tests` / `-s bt_planner/tests` / M2 `bt_scheduler_decision/tests` | 239 / 199 / 56 OK (untouched by M3) |
| `python -m unittest discover -s tests` (methodology) | 880 OK (3 opt-in real tests skipped) |
| `BITACORA_M3_REAL=1 … tests.test_scheduler_executor_real` (bounded, 1 tiny prompt each) | OK: claude haiku via `claude-personal` 14.5 s, $0.0048; codex gpt-6-luna low 14.1 s, 20 748 tokens; gemini-3.8-flash-low via `agy` 6.2 s, 12 158 tokens; all `finished/clean`, handoff captured. Raw: `real-results.json`. The ambient `claude-work` account was correctly refused for a throwaway repo outside a work project. |
| `python -m unittest tests.migration.test_package_install` | 11 of 12 OK incl. the new executor-from-wheel test. The 1 failure is M2's new modules (`bt_scheduler_laya*`, `bt_scheduler_benchmark`, `bt_scheduler_bench_local`) missing from `py-modules`: M2's pending packaging, not M3. |

## Reviews (independent, 3 fresh agents: spec, standards, adversarial)
~45 findings. Blockers/majors fixed with regressions (`tests/test_hardening.py`, adapter tests): relaunch over a live orphan from PREPARING, untracked agent after a failed spawn, double settle, NaN/inf timeouts, hostile attempt ids (invalid refs, dir collisions), hostile files (FIFO/symlink/oversized), base pinned at accept time, setsid stragglers, `/proc` read errors ≠ dead, handoff failure never a silent success (+3 retries), per-attempt event ordering, read-only CLI, private permissions, query never emits/signals, gate before side effects, effort per provider, inherited credentials, test gaps (real tests now fail on a mis-invoked CLI; stray-process assertions).

## Limits (also in the README, not hidden)
POSIX/Linux only (identity via `/proc`, `ps` fallback untested elsewhere); same-uid trust boundary and permission-bypass provider modes (as the existing supervisor); descendants that `chdir` away and leave the process group escape the sweep (no subreaper without `ctypes`); an agent whose shim dies in the microseconds before `shim.json` is untracked; `git add -A` snapshot has no size cap; slow sink delays the supervisor; Codex "clean" = exit 0 with output; events reach M1 through the adapter until M4 exists; `route:<id>` needs M2's lookup (hook ready, P-027); standalone `gemini` CLI unsupported (Gemini = `agy`).

## Not done / proposals
- Nothing committed or pushed (not requested). M1 contract 1.1.0 changes in `bt_scheduler_core` belong to the parallel M2 work.
- Proposal 1: wire M2's route lookup when `bt_scheduler_decision` lands (P-027). Proposal 2: macOS/`ps` identity tests. Proposal 3: a subreaper helper outside the stdlib-only module for full descendant control. Proposal 4: bump PLAN revision 2 so task verify commands use `discover -s` (rev 1 lists dotted module names that need `-I` off).

## Final consolidated run (2026-10-14, one pass, no edits afterwards)
Module 243 OK (lone copy + README table included) · core 239 OK · planner 199 OK · M2 `bt_scheduler_decision` 56 OK · methodology `discover -s tests` 893 OK (3 opt-in skipped; includes adapter 37, integration, M2 tests) · packaging `tests.migration.test_package_install` 12/12 OK on the live repo (M2's new `bt_*` modules, incl. `bt_scheduler_bench_quality`, were added to `py-modules` so the gate passes; M2 must keep it current) · real CLIs (opt-in, bounded): antigravity direct:gemini/gemini-3.8-flash-low finished/clean 6.8 s 12160 tok; claude direct:claude/haiku@claude-personal finished/clean 8.6 s $0.0044; codex direct:codex/gpt-6-luna#low finished/clean 8.2 s 20768 tok.

## P-033 follow-up (2026-10-15)

The shim now samples `/proc` while the agent is alive and atomically records up to 4,096 observed descendant PID/start identities in `descendants.json` (scan cap: 16,384 process entries; interval: 0.1 s). Settle validates the record before using it to identify an orphaned agent terminal. The sweep opens a pidfd, rechecks current identity/cwd/terminal ownership, and signals through the descriptor. If pidfd support is unavailable, interactive processes are preserved. `spare_interactive=False` keeps its explicit unconditional sweep behavior. A recycled PID cannot redirect a terminal-process signal.

Independent spec and standards reviews approved the scope and the pidfd race fix.

| Command | Result |
|---|---|
| `cd skill/scripts && python -W error::ResourceWarning -I -m unittest discover -s bt_scheduler_executor/tests` | 272 tests OK, including the isolated-copy run |
| `cd skill/scripts && python -W error::ResourceWarning -m unittest tests.test_scheduler_executor_adapter tests.test_scheduler_executor_integration tests.test_scheduler_chain_e2e tests.test_scheduler_integrator tests.test_scheduler_integration` | 138 OK |
| `python -W error::ResourceWarning -m unittest tests.migration.test_package_install.InstalledRuntimeTests.test_executor_module_runs_standalone_from_the_installed_wheel` | 1 OK |
| `python -m compileall -q skill/scripts/bt_scheduler_executor` and `git diff --check -- skill/scripts/bt_scheduler_executor skill/references/modules.md` | OK |
| Focused `ruff check` on changed module/test files | 6 existing findings remain in unchanged legacy lines; no new finding in the P-033 changes |
| `python -W error::ResourceWarning -m unittest tests.migration.test_package_install` | Initial run exposed `bt_plan_adapter_evidence.py` missing from `pyproject.toml`'s `py-modules`; added it, then reran the package/install suite: 13 tests OK. This helper belongs to the Planner adapter used by the integrated M1/M3 path; the isolated M3 module remains independent. |

Known sampling limits remain: a daemon re-parented between scans or one that changes cwd away from the worktree can escape. P-033 commit `9849dfe` was included in the successful fast-forward push of `main` to `939288d`. M4/M5 remain future modules, and P-001 stays deferred by the owner.
