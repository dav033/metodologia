# REQ-019 — first real run on the scheduler: what happened, what the panel does not show

_Written 2026-10-19 10:35 by session `8eef50ee` (project `dev`, supervising `pictures` REQ-019). Facts come from the
stores named in each section; commands to re-read them are in §2. Nothing here is committed to any repository._

## 1. State at 10:35

- Plan **REQ-019** (Taller 3D viewer fix, mobile usability, React Bits) runs on the scheduler since 06:38 (about four hours), on
  **plan revision 7**. **14 of 16 tasks accepted** by the independent verifier (M6): T1–T13 and T16. **T14** (full gate) is running
  on `codex-2`; **T15** (rebase and push to `main`) waits for it.
- Nothing has reached `main` of `pictures` yet. The only outward action left is T15's push (§9).
- Disk `/home` (btrfs) is at **98 %, 9.7 GiB free**, down from 14.5 GiB at 08:30: the run costs about 1 GiB per hour (§8).
- 35 attempt ids were issued; 32 reached the executor, 3 were refused at start; 26 verdicts: **16 PASS, 9 FAIL, 1 NEEDS_REVIEW**.

## 2. What the visual panel does not show, and where I found it

| What I needed | Where it lives | How to read it |
|---|---|---|
| Why an attempt was rejected (command, exit code, real output) | M6 store `~/bitacora/.state/scheduler/pictures-REQ-019-<id>-modules/m6-quality.sqlite3`: `requests.result_json`, `artifacts` (stdout/stderr by digest) | `sqlite3 -readonly <db> "select idempotency_key,state from requests"`; the checks and their `stdout_ref`/`stderr_ref` are inside `result_json` |
| Real model, account, effort, duration per attempt | Executor ledgers `~/bitacora/.state/executor/pictures-REQ-019-r<rev>-<hash>-<born>/ledger.db` (`attempts.route`, `started_at`, `ended_at`) | one root per plan revision; same trailing number = same core run |
| Every scheduler decision, retry, block, operator action | `~/bitacora/.state/scheduler/pictures-REQ-019.db`, table `audit` | `select seq,kind,task_id,attempt_id,detail from audit order by seq desc limit 50` |
| The exact prompt and brief an agent got | `…/executor/<root>/attempts/att-NNNN-<hash>/prompt.txt`, `brief.json` | read the files |
| The agent's own words and last output | same folder: `report.json`, `output.log` | `tail -c 3000 output.log` |
| Why the scheduler process died | `~/.local/tmp/claude-1000/req019-run.log` (faulthandler dump) | `Bus error` = disk; `StoreError storage_pressure` = M4 store cap |
| M4 monitor store size, WAL, incidents | `…-modules/m4-monitor.sqlite3(-wal)` | `ls -la`, `select count(*) from normalized_events` |
| Frozen plan revisions | `~/bitacora/pictures/requirements/REQ-019-*/plan-revisions/PLAN.r1…r7.json` | `bitacora.py --project pictures plan-json show REQ-019` |
| Account quota and load | `bitacora.py usage`, `bitacora.py agents route --kind implement --complexity M` | prints pressure per account and the chosen route |
| Disk and btrfs allocation | `sudo btrfs filesystem usage /` | «Device unallocated» is the number that matters |

The panel (`plan-status`, `/plans`) shows task state, model and account of the **current** attempt. It does not show attempt
history per task, rejection evidence, the verifier sandbox, the M4 store, plan revisions, or operator interventions.

## 3. Timeline (local time, 2026-10-19)

| Time | Event (audit log of the scheduler) |
|---|---|
| 06:38 | REQ-019 launched (`handoff`), plan r1. Every task routed to `gpt-6-luna` on `codex-1`; the owner noticed. |
| 06:40 | I paused the run; router analysed and fixed (D-002). 06:49 resumed; resume failed twice in M4 (D-003). |
| ~07:05 | Verifier rejected the snapshot (`export-subst`, D-004); sandbox could not run Node, `CHECK_UNAVAILABLE` (D-005). |
| 07:35 | Plan **r2** applied (no manual checks, D-006); the rebase hit three scheduler bugs (D-007). |
| 07:48 | **First task accepted by the independent verifier** (T1, attempt 3, `codex-luis`). |
| 07:5x–08:10 | T2, T3, T4 accepted after retries; scheduler died twice with `Bus error` (btrfs, D-008). |
| 08:10 | Plan **r3**: T5's check hit `ERR_CONNECTION_REFUSED` (T4's audit needed a dev server) (D-009). |
| 08:19 | T6 accepted in under a minute on a keyboard-only check; 08:27 plan **r4** adds T16 (D-010). |
| 08:34 | Plan **r5**: `INTEGRATION_CONFLICT` between T7 and T8 on the audit script → one straight chain. |
| ~08:45 | Scheduler died on `storage_pressure` (M4 store at its 512 MiB cap, 47 000 stderr incidents) (D-011). |
| 08:51 | T16 attempt 2 fixed the sheet's snap bug that the new oracle exposed; accepted 08:54. |
| 09:02–09:07 | T9 rejected (`LayoutProps`, type debt); verifier now runs `next typegen`; plan **r6**. |
| 09:32–09:50 | T10 retried once; T11 failed twice because it never wrote its test; plan **r7**; scheduler died again on the M4 cap (D-012). |
| 09:57–10:26 | T11, T12 and T13 accepted (T13, the measurements, took 23 min). |
| ~10:25 | Publication step enabled for T15 only (D-013). 10:26 T14 (full gate) started on `codex-2`. |

## 4. Failures found, with cause, fix and test

**Router and policy** (`bt_role_routing.py`, `bt_role_policy.py`)
1. Implementer ignored complexity; inside a family the account came from pool order (46 % chosen over 17 %); no memory of
   sessions placed. Fix: high complexity prefers `sonnet medium`; each account ranks by paced pressure + 4 points per
   session of the last 5 h (cap 40). Tests: `tests/test_role_routing.py` (22). D-002.
2. The load counter read `bt_events`, which scheduler sessions never reach (latest row: 16 Oct). Fix: it also reads every
   executor ledger, running sessions included. Same tests.

**Monitor M4**
3. A replayed gap with a new `recorded_at` raised `gap_id replay has different or regressing content` (D-003).
4. A replay behind the stored cursor raised `cursor cannot regress`. Fix: keep the stored cursor on the same boot (D-003).
5. Every plain-text stderr line became a `malformed_json` gap event **and** an `info` incident: 47 000 incidents, thousands of
   audit rows in M1, a 365 MiB WAL, scheduler dead at the 512 MiB cap. Fix: no incident, then no event (cursor only), and
   `journal_size_limit` 64 MiB (D-011, D-012). WAL went from 313 MiB to ~80 KiB.

**Verifier M6**
6. `export-subst` files (`version-codigo.json`, `version_codigo.json`) never matched their blob: restored from the blob
   and verified with the same digest (D-004).
7. Sandbox had only `/usr`: now Node (found on `PATH`), Playwright cache, the attempt's `node_modules`, the worktree's
   git metadata, all read-only; `NODE_OPTIONS` heap 6 GiB; `RLIMIT_DATA` 12 GiB instead of a 2 GiB address-space cap;
   1024 files, 512 processes; command 1500 s, total 3600 s (D-005).
8. An attempt without its own `node_modules` now falls back to the repository's only when `package-lock.json` is
   byte-identical. Workspace packages are built and `next typegen` is run inside the sandbox before every check, because
   `packages/*/dist` and the route types are git-ignored (D-005, D-012).
9. Same command serving several criteria ran once per criterion; now once.

**Scheduler**
10. `--rebase` then `--resume` failed with `PLAN_MISMATCH` (runtime marker kept the r1 hash): `rebind_runtime` (D-007).
11. First attempt of a new revision was treated as a retry of an old revision's attempt, and a start the executor never
    accepted also blocked the retry: both fixed in `bt_scheduler_retry.py` (D-007).
12. After a rebase, kept tasks' snapshots lived in another revision's executor root (`PREDECESSOR_HANDOFF_MISSING`): the
    lookup now reads sibling roots of the same core run, read-only (D-009).
13. `max_attempts` was 1: any failure blocked the plan. Now 3 (`scheduler.max_attempts`, `scheduler.max_parallel_tasks`
    stays 1) (D-012).
14. Agents were told never to push, which made T15 impossible; only the task whose frozen check is
    `git merge-base --is-ancestor HEAD origin/main` may push once to `main` (D-013).
15. Agents were never told that a check script that does not exist yet is theirs to create (T11 failed twice).

Not explained: every resume logs `port_error … AttributeError … query` once per live attempt (harmless, P-007).

## 5. Plan revisions

| Rev | Why |
|---|---|
| r1 | Original, 15 tasks, manual checks, T1/T4 verified commands that fail by design |
| r2 | Owner: nothing manual. Every criterion → one command; `--base`, `--autoprueba`, `--solo`; T7 low→medium |
| r3 | T4's audit must be self-contained (no dev server); constraint added for all UI oracles |
| r4 | New task T16: the audit did not prove touch drag, velocity snap, reduced motion, camera offset |
| r5 | DAG serialised: T7/T8 conflicted on `test-ui-taller-movil.ts` (one task at a time anyway) |
| r6 | T9 owns the type-check debt; T10–T12 re-run `tsc` |
| r7 | T10–T12 list their test script; T11/T12 say they create it |

## 6. Attempts (executor ledgers)

32 attempts: **22 on `codex-luis`/`gpt-6-luna`, 7 on `claude-work`/`sonnet`, 1 each on `codex-1`, `codex-2`, `claude-personal`.**
Five rows show `running` forever (`att-0011, 0017, 0020, 0025, 0031`): I cancelled those attempts by hand and stopped
their agents, the ledger was never closed.

Verdicts: 16 PASS, 9 FAIL, 1 NEEDS_REVIEW. Of the 10 non-passes, **5 were our infrastructure or plan, 5 were real defects**:

| Attempt | Task | Cause |
|---|---|---|
| 0001 | T1 | sandbox had no Node (infra) |
| 0004, 0005 | T2, T4 | attempt had no dependencies for the verifier (infra) |
| 0010 | T5 | the audit needed a dev server (plan/oracle) |
| 0024 | T9 | `LayoutProps` not generated + type debt of earlier tasks (infra + debt) |
| 0007 | T3 | WebGL context-loss test timed out waiting for the camera (**real**) |
| 0022 | T16 | slow release ended at 717 px instead of the medium step — found by the new oracle (**real**) |
| 0027 | T10 | test script missing, type error in `GrillaCompacta.tsx` (**real**) |
| 0029, 0030 | T11 | test script missing twice (**real**, prompt gap) |

Agent time per accepted attempt: 0.5–23 min; most of the wall clock went to verification (type check ≈ 66 s, phone audit
≈ 11–17 s per check, gate ≫ 10 min) and to infrastructure fixes.

## 7. Distribution across accounts and models — not solved

The owner's complaint was that a whole plan went to one model and one account. After the fixes: high-complexity tasks T6/T12
went to `sonnet`; retries moved to `claude-work`; four accounts were used. But **22 of 32 attempts (69 %) still ran on
`codex-luis`**, because it has the lowest quota pressure (17 % vs 23–27 %). The load penalty (4 points per session in 5 h,
cap 40) is too gentle to rebalance that gap while sessions age out of the window. Open: P-009.

## 8. Machine facts

- `/` and `/home` are one btrfs filesystem, **98 % used, 9.7 GiB free**. All chunks were allocated (93 MiB unallocated) when
  SQLite started dying with SIGBUS; I ran `btrfs balance -dusage=10` and `-dusage=30` (unallocated now ~2 GiB). The
  next failure of this kind is a full disk. Biggest consumers I saw: `~/bitacora/.state/runs` (2.1 GiB), `executor` roots
  with one `node_modules`/worktree per attempt (1.4 GiB and growing), `~/.local/tmp/claude-1000` (600 MiB, partly mine).
- M4 store: 223 MiB (cap 512 MiB), WAL ~80 KiB.
- The verifier runs each check in a fresh `bwrap` namespace: no network, no home contents, `/workspace` tmpfs 1 GiB.

## 9. What T15 will do (outward action)

Authorised by the owner in REQ-019 round 1, Q2 («push directly to `main` after the local gate»), and by the approved plan. T15
starts only if T14 is accepted. The agent fetches, rebases onto `origin/main`, runs the checks, commits and runs
`git push origin HEAD:main` once, fast-forward only, never `--force`, no other branch or tag. The verifier then checks
`git merge-base --is-ancestor HEAD origin/main` and `git diff --quiet HEAD origin/main`. Expected side effects, per the
plan: `checks.yml` runs on the push and Vercel likely builds Production from `main`. The VPS deploy is manual and not run.

## 10. Code touched (skill repo `~/dev/metodologia/skill/scripts`, nothing committed)

Mine: `bt_role_routing.py`, `bt_role_policy.py` (both untracked), `bt_scheduler_quality/{sandbox_mounts,sandbox_prepare}.py`
(new) and `{policy,engine,runner,runner_execution,runner_sandbox_process,snapshot,snapshot_git,snapshot_tree}.py`,
`bt_scheduler_quality_adapter.py`, `bt_scheduler_monitor/{detectors,store,stream_store}.py`,
`bt_scheduler_m4_stream_bridge.py`, `bt_scheduler_retry.py`, `bt_scheduler_executor_adapter.py`,
`bt_scheduler_executor/{prompt,model}.py`, `bt_scheduler_run.py`, `bt_cli_scheduler_run.py`, `bt_config.py`.
Tests added or changed: `tests/test_role_routing.py`, `bt_scheduler_quality/tests/{test_runner,test_engine,test_snapshot,
test_adapter,test_review}.py`, `bt_scheduler_monitor/tests/{test_store,test_detectors}.py`,
`tests/{test_scheduler_runtime,test_scheduler_recovery_sources,test_scheduler_monitor_runtime,test_scheduler_m3_stream_wire,
test_scheduler_publication}.py`, `bt_scheduler_executor/tests/test_prompt.py`.
The same working tree holds other sessions' uncommitted work (executor `config/handoff/settle/spawn`, monitor `queries`, …):
review before committing. Suites re-run green after each change; `tests/test_audit_routing.py` has 3 failures that predate
all of this (P-005).

## 11. Risks and open items

- **P-006** disk at 98 %: free several GiB before the next plan.
- **P-007** unexplained `AttributeError` in the executor `query` port on every resume.
- **P-008** an oracle written by the agent that builds the feature can be weaker than the criterion (T6 passed on keyboard-only
  checks); the verifier reads exit codes only.
- **P-009** distribution is uneven (§7).
- **P-010** the publication step is detected from the verification text, not from a declared plan field.
- **P-011** five ledger rows stay `running` after a manual cancel; executor roots and worktrees are never cleaned.
- The M4 store still keeps ~83 000 old gap events and 47 000 old incidents of this run (retention is 90 days).
- Ten tasks changed the audit/test scripts of earlier tasks; the final gate (T14) is the first time the whole set runs together.

## 12. Candidate learnings for the diary

1. A module can be green on its own tests and still fail on its first real path: this run found ~15 defects at module seams
   (sandbox ↔ repo layout, rebase ↔ executor roots, monitor ↔ CLI stderr). A smoke test with a real minimal JS repo is missing.
2. A verifier that trusts exit codes verifies exactly what the builder's oracle checks; audit each oracle against its criterion.
3. Every plan revision needs its own executor root; anything that spans revisions (snapshots, retries) must say how.
4. Disk pressure on btrfs shows up as SIGBUS in SQLite, not as ENOSPC.
5. Tell the agent what the verifier will do and that missing check scripts are theirs; do not assume.
6. In my own handling: `pkill -f` can match the shell that runs it; killing the first `pgrep` hit twice hit the wrapper, not the
   interpreter. Use the exact command line.
