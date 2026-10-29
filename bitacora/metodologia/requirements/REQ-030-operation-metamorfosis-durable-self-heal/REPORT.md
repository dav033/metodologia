# REQ-030 — Operation Metamorfosis: report

Date: 2026-10-28. Iteration 1: branch `metamorfosis` (fast-forwarded into `main` at `003b7d6fc`). Iteration 2 (the ten
pending items of [CONTINUE.md](CONTINUE.md)): branch `req030-final` at ``e5ba3758b``, merged into `main` as ``3519eec09` (pushed; deployed 22:12)`.
Raw requirement: [REQUEST.raw.md](REQUEST.raw.md). Baseline and map: [M0-ARCHAEOLOGY.md](M0-ARCHAEOLOGY.md). Package
documentation: `skill/scripts/bt_durable/README.md`. Commands below run from `~/dev/metodologia` with
`PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest <module>` and `BT_LAB_DIR` set to a scratch
directory.

## Two runtimes, one owner per run

| | Legacy runtime (Scheduler owner, stdlib) | Durable runtime (DBOS + systemd + Pydantic) |
|---|---|---|
| Owns | pictures REQ-020 (29 completed, 2 pending, 1 blocked) and the finished REQ-019, REQ-027, REQ-029 | pictures REQ-021 r15 (`RUN.owner.json` backend `dbos`) |
| Processes | watchdog + monitor services per run, outboxes, hold file | `bt-durable.service` (one engine), PostgreSQL `metodologia-dbos-pg`, one systemd unit per agent attempt |
| Changes in iteration 2 | none to its behaviour (the design-notes change was reverted there, 73eb93b3c); file guard after shell commands (item 8) | items 1–8 below, plus the fixes of the review |
| Removal | proposed in `DECISIONS.md` D-144 (nothing removed) | — |

A run has exactly one owner: `RUN.owner.json` is claimed by compare-and-swap at migration and the legacy owner refuses a
run the durable runtime owns.

## Iteration 2: the ten items

| # | Item | State | Evidence |
|---|---|---|---|
| 1 | Subplans and composition gates (1.3.0) | done | `test_durable_subplans` (8): per-subplan lines hold their scope, a member starts from its line, the gate task starts from the composition candidate (bt_composition) and work after the gate waits for it; the migration keeps each subplan's line; atomic multi-line integration; the run survives a failing line sync or composition. Live: REQ-021 turned subplans on at its first turn after the 22:12 restart (`subplans_enabled` 22:16: SP-1, SP-2, SP-14, SP-3; gates CG-1, CG-4, CG-2) and created its four subplan lines from the pin `fa101a47` with no conflict |
| 2 | Brief parity with legacy | done | `test_durable_briefs` (3): no section of the legacy prompt is missing from the durable one; the live REQ-021 T2.6 brief carries `RUN.notes/T2.6.md`. The legacy runtime keeps its prompt (design-contract notes stay out of it, 73eb93b3c); the durable brief carries them |
| 3 | Manual checks with attestations | done | `test_durable_attestations` (2): a valid receipt settles the manual check without asking; a missing one is a decision with `reverify` and `bt-durable attest` passes the same snapshot. Live: REQ-021 T3.2 completed at 22:19 by `bt-durable answer pictures REQ-021 T3.2 T3.2:d1@k1 reverify`: the owner's receipt bound to legacy att-0059 settled its manual check on re-verification, no agent run |
| 4 | Milestone audit → coordinated remediation (scenario K) | done | `test_durable_audits` (3 e2e + 2 pure): related findings become one repair with probes, re-audit, bounded rounds, panels show a held audit; `test_durable_audits_upgrade` (2): an engine upgrade replays an old audit unjudged and judges a new one. REQ-021's audits declare their ledgers; live policy `ledger_required`, `read_only`, `remediate`, 2 rounds. Live: REQ-021 T2.7 judged three times, its findings grouped into coordinated repairs (T2.3, T2.4, T2.5), held blocked at the round limit with its reason in the panel; the engine-owned ledger check fixed on the way (`992d1706d`) |
| 5 | Router with the M2 decision engine, LiveQuota as capacity | done | `test_durable_router` (13): an account without quota is never chosen and the other runs without spending an attempt; the decision is the `route_decision` telemetry event |
| 6 | Panels show durable runs; remote commands as durable messages | done | `test_durable_remote` (9): projection sequencing, a stale command refused at the ledger and by the run workflow, an old recorded pause replays; `test_remote_contracts` (15) validates the snapshot of a real durable run. Live: the web dashboard (`/api/plans/pictures/REQ-021`) shows REQ-021 with authority `dbos`, status `running`, T2.6 and T3.11 running with their attempt ids; the remote snapshot built by the deployed release validates against `RemoteSnapshot` with REQ-021 in it |
| 7 | Plan/subplan contracts in Pydantic | done | `test_plan_contract_models` (15): every frozen plan of the bitácora gets the same verdict from the runtime loader and the planner; each known defect (`req`/`req_id`, array/object, unknown state) is refused before anything is enqueued; generated JSON Schema is fresh |
| 8 | File guard for shell writes | done where reliable | `test_file_guard` (10): git-based crossing check after shell commands, once per session; `test_durable_file_guard` (4): capture-time check in the durable runtime (`file_guard` event, `Snapshot.oversized`). Not covered: writes outside a git work tree |
| 9 | Retire duplicated legacy infrastructure | proposed, nothing removed | `DECISIONS.md` D-144: six groups with their durable equivalent, evidence and removal condition; the hold file is not yet equivalent. Removal waits until REQ-020 is migrated or closed and REQ-021 completes on the durable runtime |
| 10 | Comparable benchmark | done | `evidence/iter2/bench-runtimes.md`: same plan, failures and agent process; legacy 12 launches / 2 owner interventions / 4 of 5 fixable tasks, durable 10 / 1 / 5 of 5; durable ~3× slower in wall time on tiny tasks |

## Review of the integrated branch and its fixes

An independent review of `3cdace8f4` ([evidence/iter2/review-3cdace8f4.md](evidence/iter2/review-3cdace8f4.md)) checked
replay safety against the live REQ-021 histories (queried read-only), the multi-line integration and launches while
paused. Found and fixed in `a6a2706c9`, each with a test that fails on `3cdace8f4`:

- a step the run workflow calls itself (`bt.sync_lines`, `bt.compose`, `bt.audit_gate`) failing after its retries
  ended the run in ERROR, which DBOS never recovers. Now behind `DBOS.patch("bt-run-survives-step-failures")` it is
  reported and retried next turn (`StepFailureInTheRun`: a stale ref lock, a missing line-base pin);
- the run line could move without its subplan lines when another writer moved one of them in between; now one
  `git update-ref --stdin` transaction (`AtomicLines`, real git);
- a subplan line that could not be created produced a fake empty "conflict" and a run without that line; now
  `SUBPLAN_LINE_UNWRITABLE`, retried;
- a run that stopped with a gate task never started was reported `completed`; now `completed` only when every task of
  the plan is done.

Verified in the same review: the live `bt.run` history starts with `bt.plan_text`; `T2.6:k1`/`T3.2:k1` replay on the
new code (each new patch meets a recorded step and returns False); nothing launches an agent while a run is paused.

## Acceptance criteria of REQUEST.raw.md (only checked with evidence)

- [x] DBOS integrated and used by a complete realistic flow — `test_durable_e2e`; with subplans, gates, attestations
  and audits: `test_durable_subplans`, `test_durable_attestations`, `test_durable_audits`.
- [x] Main contracts validated with Pydantic — runtime, remote and now plan/subplan contracts (`test_plan_contract_models`).
- [x] Agent processes supervised by a Linux runtime — `bt_supervisor` (systemd units, process-group fallback); kill
  lists scoped to their own supervisor (e2d961ee5); the engine's own unit variables never reach an agent (366cbf372).
- [x] Recovery with real interruptions — engine SIGKILL mid-attempt (0 duplicate launches), PostgreSQL outage, engine
  upgrade mid-run from the live engine's code (`test_durable_upgrade`, `test_durable_audits_upgrade`).
- [x] Reconciliation of external effects — adoption per attempt key, CAS integration (one transaction across lines),
  one M6 verdict per verify key. Exactly-once is NOT claimed.
- [x] Concurrency and worktrees protected — resource claims, one worktree per attempt, cancellation stops writers.
- [x] Retries and self-repair with limits — Hypothesis budget property; audit remediation rounds bounded.
- [x] Preventive plan verification — `bt_planner.preflight` and the Pydantic plan contract before `bt-durable start`.
- [x] Remote control compatible with the new runtime — durable runs in the remote panel and web dashboard, commands as
  durable messages with request id and precondition (item 6).
- [x] Migration of legacy plans tested — unit + e2e; applied to pictures REQ-021 (28 inherited).
- [x] Safe workflow versioning — `test_durable_versioning`; every iteration-2 change to `bt.run`/`bt.task` is behind a
  patch placed before a plain step, proven by the upgrade tests.
- [x] Adversarial tests executed — chaos table below.
- [x] Existing regressions controlled — full suite before integrating (below).
- [x] Dependencies registered and locked — `uv.lock` (dbos 3.3.0, pydantic, psutil; dev hypothesis, ruff).
- [x] Linux installation, recovery and rollback documented — `bt_durable/README.md`.
- [x] Comparative metrics — item 10 (same plan in both runtimes) and the per-mechanism comparison of iteration 1.
- [x] No completeness claimed for unvalidated parts — "Not done / remaining debt" below.

## Chaos and adversarial evidence

| Scenario | Test | Result |
|---|---|---|
| B agent running when the engine dies | `test_engine_sigkill_mid_attempt_recovers_without_a_duplicate_launch` | 1 launch, run completed |
| C work done, checkpoint missing | supervisor adoption tests + B | adopts the unit, no second process |
| D step recorded, then crash | B | recorded steps not re-run |
| E duplicate concurrent commands | `test_duplicate_concurrent_answers_start_one_attempt`, `test_remote_commands_are_durable_idempotent_and_refuse_stale_views` | one attempt; stale ids and stale views refused |
| F cancel while writing | `test_cancelling_a_run_stops_every_writer` | writer stops, no marked process |
| H database outage | `test_durable_postgres` | completed, 1 launch |
| I workflow version change | `test_durable_versioning`, `test_durable_upgrade`, `test_durable_audits_upgrade` | old histories keep their steps; new paths only past the patch |
| J repeated migration | migration tests | no-op, legacy stores untouched |
| K audit with related findings | `test_durable_audits` | one coordinated repair for F1+F2, re-audit passes; never-clearing audit stops at its round limit |
| L quota exhausted | `test_no_capacity_waits_durably_for_the_reset_then_runs`, `test_an_account_without_quota_is_never_chosen_and_the_other_runs` | durable wait; the other account runs |
| M worktree reused | `GitWorkspaces` manifest check | refused (`WORKSPACE_ERROR`) |
| N permission | classifier/policy tests | always escalated |
| O infra vs code | environment repair vs retry tests | re-verify (1 launch) vs retry (2 launches) |
| step failure inside the run | `StepFailureInTheRun` (2) | run survives, retried next turn, completes |
| concurrent writer on a line | `AtomicLines` | no line moves alone |
| A, G | frontier tests (Hypothesis) | ready tasks never conflict; nothing restarts a known task |

## Regression before integrating

[evidence/iter2/regression-final.txt](evidence/iter2/regression-final.txt): every test file in its own process
(own `BITACORA_ROOT`/`BT_LAB_DIR`), on `a6a2706c9`: 268 files, 5 fail. Four are baseline failures
(`test_plan_boundary` with the same planner imports as `main`, `test_real_designer_kit`, `test_recovery_views`,
`test_remote_panel`); `test_plan_schema_13_compat` and `test_platform` no longer fail. The fifth,
`test_durable_postgres`, was a race of the test under load (enqueue before the engine finished the DBOS schema): it
passed alone twice and passes since the test retries the idempotent start (`e5ba3758b`). `test_stdlib_boundary`
passes. The earlier run on `req030-item4` is [evidence/iter2/regression-item4.txt](evidence/iter2/regression-item4.txt).

## Benchmark (no invented numbers)

Iteration 2, same plan in both runtimes ([evidence/iter2/bench-runtimes.md](evidence/iter2/bench-runtimes.md)), three
runs on `main` and one on the integrated code, counts identical in all four:

| Metric | Legacy | Durable |
|---|---|---|
| Agent launches | 12 | 10 |
| Launches beyond the unavoidable ones | 2 (T3 ×3, then blocked `m5:attempts_exhausted`) | 0 |
| Owner interventions | 2 | 1 |
| Fixable tasks completed | 4 of 5 | 5 of 5 |
| Tokens (fake agent, 120 per launch) | 1,440 | 1,200 |
| Recovery T2 / T3 / T4, s | ~1.2–1.7 / never / ~4.6–5.1 | ~4.1–4.3 / ~2.1–3.1 / ~5.3–6.5 |
| Wall time, s | 8.2–9.1 | 28.8–32.4 |

Observed: the whole difference in launches and interventions is the environment failure (verifier heap OOM), which
legacy treats as a code failure. Observed: durable is ~3–3.5× slower on six tiny tasks. Hypothesis (not measured per
mechanism): polling and one systemd unit per attempt. Iteration 1's legacy REQ-021 numbers (71 attempts, 34 verify
failures, T2.6 alone 24 attempts) stay as recorded in its own stores.

## Live state at the end

Deploy of 2026-10-28 22:11–22:30 ([evidence/iter2/pre-deploy.txt](evidence/iter2/pre-deploy.txt)):

- Safety step: DBOS dump `~/bitacora/.state/durable/backups/bt_durable-20261028-221114.dump` (sha256 `a8e299b9…`,
  `pg_restore --list` readable); previous `main` `646cb7126`, previous remote API release `003b7d6fc`; rollback
  procedure in the same file.
- `main` → `3519eec09` (merge of `req030-final`), pushed. `bt-durable.service` restarted 22:12:48: DBOS recovered the
  3 REQ-021 workflows, none ended in ERROR. `bitacora-web.service` restarted. Remote API release
  `~/.local/share/bitacora-remote/3519eec09…` (drop-in backup `exec.conf.bak.20261028-003b7d6f`). Vercel rebuilt the
  phone from `main` (success). Gateway unchanged (its code did not change; the schema change is additive).
- Smoke: engine log without errors; REQ-021 projection written; web API and remote snapshot show REQ-021 (above);
  `remote/deploy/smoke.py --live`: same result as the previous release (`partial`: probes that need the owner's
  session or Telegram credentials not run; negative paths pass).

pictures REQ-021 r15 — durable runtime, running (timeline from telemetry):

- 22:19 owner `T3.2:d1@k1 reverify` → T3.2 completed by its att-0059 receipt, no agent run (item 3).
- 22:19 owner `T2.6:d1@k1 retry`, run resumed. T2.6 a2 (from its legacy snapshot att-0095, brief carrying
  `RUN.notes/T2.6.md`, item 2; routed by M2 `route_policy_preferred` → `codex:codex-luis:gpt-6-luna`, item 5) was
  accepted at 22:37 and went into the run line, SP-2 and SP-14 and not into SP-3 (item 1). In the legacy runtime this
  task had used 24 attempts.
- Agent processes carry their own unit's `INVOCATION_ID` and `BT_SUPERVISOR_ID`, and no `BT_DURABLE_*`/`DBOS_*`.
- Two verifier defects found live and fixed (details: [evidence/iter2/live-req021-m6.md](evidence/iter2/live-req021-m6.md);
  regression [evidence/iter2/regression-m6-fixes.txt](evidence/iter2/regression-m6-fixes.txt): 269 files, only the 4
  baseline failures; third deploy 23:34 with a DBOS backup first, `main` `bc7425690`):
  - every REQ-021 audit checks its ledger with `bitacora.py audit-ledger check`, which the durable verifier ran in the
    product sandbox (`M6_SETUP_ERROR:EXEC`); now answered by the engine as in the legacy runtime (`992d1706d`);
  - checks inherited the engine's environment (`verifier.inherit_env: ['*']`), including `VK_DRIVER_FILES` from the
    desktop session — Chromium's software WebGL could not start, so T3.11 failed in every attempt of both runtimes —
    and the engine's database URL; now filtered (`a6174efa7`).
- T3.11: its a4 snapshot passed the real check through the real M6 runner once the environment was fixed; owner
  `reverify` twice (M6 marks the first pass after a failure as flaky and confirms on the second) → completed 23:47, no
  further agent attempt; in the run line and SP-3 only.
- T2.7 (SP-2 visual audit) — item 4 live: a2, run with the operator's note authorizing the repository's UI harness and
  Playwright, was judged by the gate at 23:40: 3 blocking findings, grouped into 3 coordinated repairs (T2.3←F1,
  T2.4←F2, T2.5←F3). The findings were in fact one environment limitation (the harness needs the REQ-021 test database,
  which no agent receives in either runtime): the three repairs made no change (snapshot = base) and the audit runs
  again (round 2, a101), bounded by `remediation_rounds = 2`. Decision for the owner below.
- 00:10 T2.7's third audit still could not render: blocked at its round limit (2 rounds, 6 repair attempts that changed
  nothing, 3 audits), held with its reason; the web panel shows it `blocked` with "auditoría bloqueada: 3 blocking
  finding(s) … after 2 remediation round(s) (limit 2)". The run goes on: T3.12 (SP-3) running.
- State at 00:15: 31 of 45 tasks done (25 inherited + T3.2, T2.6, T3.11 and the no-change repairs of T2.3, T2.4, T2.5),
  T2.7 blocked, T3.12 running. The composition gates (CG-1 → T91, CG-4 → T94, CG-2 → T92) all depend on T2.7/T2.8, so
  no candidate can be composed until the owner decides on T2.7 (see "Blocked"); composition itself is proven end to end
  in `test_durable_subplans`.

Legacy runtime: pictures REQ-020 revision 22 (29 completed, 2 pending, 1 blocked) held since 2026-10-25 ("operator
stop"); REQ-019, REQ-027, REQ-029 finished. Their services and stores are unchanged.

## Blocked, with reason and procedure

- REQ-021's visual audits (T2.7, T14.5) cannot render the candidate: the repository's UI harness needs
  `PICTURES_REQ021_DATABASE_URL` (the dedicated REQ-021 test database), which the verifier receives (operator env file)
  but no agent does, in either runtime. Reason it is not decided here: it gives agents a database credential. Procedure
  for the owner: either add `PICTURES_REQ021_DATABASE_URL` to the environment visual-audit agents receive (the durable
  M3 adapter's agent environment), then `bt-durable retry-task pictures REQ-021 T2.7` (one more round); or review the
  SP-2 screens yourself and record the ledger's findings as `accepted` with `accepted_by: owner` and a reason.
  Lesson recorded: the operator's note told the auditor to record states it could not capture as open findings, so
  the gate would not read an empty ledger as a pass; the gate then sent an environment limitation to product tasks as
  repairs (harmless here: no change, but 6 attempts). An audit that cannot capture should stop as an owner decision,
  not as findings against product tasks: proposal below.

- Phone panel signed in, and the credential-only probes of the live smoke (`signin-start`, `sse`, `telegram-delivery`:
  `ok: false` in `remote/deploy/receipts/live-smoke.json`, the same as for the previous release). Reason: they need
  the owner's GitHub session or the Telegram bot token, which agents may not read or use. What was verified without
  them: the negative paths of the live smoke pass, and the snapshot the deployed remote API serves (built with the
  release `3519eec09` code) validates against `RemoteSnapshot` with REQ-021 in it. Procedure for the owner: sign in at
  https://flow-remote.vercel.app on the phone (360 px), open pictures REQ-021 and check that it shows the durable run
  (state, attempts, open decisions); then run `python remote/deploy/smoke.py --live` from a shell that has the owner's
  session to complete the receipt.

## Not done / remaining debt

- Proposals for the owner (not done): (1) the legacy verifier inherits the same session variables as the durable one
  did (`VK_DRIVER_FILES`), so its WebGL checks fail the same way: apply `adapters/m6.sandbox_policy`'s filter in
  `bt_verifier_env.ambient_for_run`, or narrow `verifier.inherit_env`; (2) a ledger status for "could not audit" that
  the gate turns into an owner decision instead of findings against product tasks; (3) the `quality_audit_evidence`
  cross-check (evidence files behind each finding) in the durable gate.

- Audit-driven plan revisions (new remediation tasks in the frozen plan) are not ported: the durable repair is a new
  round of an existing task. The `quality_audit_evidence` cross-check is not ported.
- The legacy publication of a composition requires an M6 proof bound to the candidate's exact tree; the durable gate
  passes when its gate task is accepted on a snapshot built on the candidate.
- The M2 router does not reserve accounts or apply per-account concurrency limits and does not persist an M2 ledger
  (telemetry is the record).
- The file guard does not see writes outside a git work tree.
- Nothing legacy was removed; D-144 proposes what to retire and when.
- A task waiting on a pause, and the run workflow itself, record a few operations per poll: long pauses lengthen
  replays (no measured impact yet).
- The subplan lines of a migrated run hold a superset of their scope (legacy snapshots bring their history).
- Exactly-once for external effects is not claimed.
