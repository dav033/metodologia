# REQ-030 item 10 — comparable benchmark of the legacy and durable runtimes

Date: 2026-10-28. Harness: `skill/scripts/tests/bench_runtimes.py` on branch `req030-bench` (`df0c18e79`, based on
`main` `986515000`). Raw results: `bench-runtimes/run{1,2,3}.{compare,legacy,durable}.json`.

## How to reproduce

```sh
cd ~/dev/metodologia            # or the worktree with the harness
BT_LAB_DIR=<scratch dir> uv run python skill/scripts/tests/bench_runtimes.py run <out dir>
uv run python skill/scripts/tests/bench_runtimes.py compare <out dir>
```

Each side runs in its own fresh process and repository; nothing touches the real bitácora, the live PostgreSQL or the
live engine (DBOS on SQLite under the scratch dir, systemd units with a lab prefix).

## What is identical on both sides

- the plan bytes: a strict 1.2.0 plan (validated by the legacy planner's publication rules) with six tasks;
- the starting repository and its checks (`durable_support.Lab`), the M6 sandbox verifier and its policy;
- the agent process: the fake `claude` (`fake_providers/durable_agent.py`) launched by `bt_driver`'s real claude
  invocation and read by its real parser, through one shared driver class;
- the injected failures and the scripted owner (it answers the decision the runtime raises with "stop").

| Task | Injected | Launches no runtime can avoid |
|---|---|---|
| T1 | none | 1 |
| T2 | implementation failure, fixed by a retry that continues from its own snapshot | 2 |
| T3 | the check fails like a Node build out of heap unless the verifier raises its heap (environment) | 1 |
| T4 | the first launch hits the provider's usage limit (reset in 3 s) | 2 |
| T5 | none, depends on T1 | 1 |
| T6 | never fixed: the runtime must stop and ask the owner | (bounded by each runtime's budget) |

What differs: only the runtime. The legacy owner runs in process with its real M1/M3/M5/M6 stores, patched only where
its own owner e2e patches it (no autostart, no notifications, the M2 route table, the repository registry, sleeps capped
at 0.5 s). The durable engine runs as its own process (DBOS on SQLite, `poll_seconds=0.5`, `max_parallel=2`).

## Observed (three runs, counts identical in every run)

| Metric | Legacy | Durable |
|---|---|---|
| Agent launches | 12 | 10 |
| Launches beyond the unavoidable ones | 2 (T3: 3 launches) | 0 |
| Owner interventions (decisions a person must take) | 2 (T3, T6) | 1 (T6) |
| Launches before the owner was asked about T6 | 3 | 3 (retry, then one coordinated remediation) |
| Fixable tasks completed (T1–T5) | 4 of 5 (T3 blocked `m5:attempts_exhausted`) | 5 of 5 |
| Tokens (120 per launch, as the fake agent reports) | 1,440 | 1,200 |
| Recovery time T2 (first failure → accepted), s | 1.6 / 1.2 / 1.2 | 4.1 / 4.3 / 4.3 |
| Recovery time T3, s | never (blocked) | 3.1 / 2.1 / 2.2 |
| Recovery time T4, s (includes the 3 s reset) | 5.0 / 5.1 / 4.6 | 6.1 / 5.4 / 6.5 |
| Wall time of the whole run, s | 9.1 / 8.2 / 8.7 | 31.4 / 30.0 / 32.4 |

Durable recovery decisions (telemetry, every run): T2 `retry` CHECK_FAILED; T3 `repair_environment` VERIFIER_OOM (the
same snapshot verified again with a bounded larger heap, no agent run); T4 `wait` ROUTE_LIMIT; T6 `retry`, `remediate`,
then `escalate` (`max_same_signature`). Legacy attempts: T3 rejected three times with M6 evidence, then blocked; T6 the
same.

## Observation vs hypothesis

- Observed: on the same plan and failures the durable runtime spent 2 fewer agent launches (−17 %), asked the owner
  once instead of twice, and completed every fixable task; the difference is entirely the environment failure (T3),
  which the legacy runtime treats as a code failure.
- Observed: the durable runtime is about 3.5× slower in wall time on this plan of six tiny tasks, and its recovery of a
  plain code failure (T2) takes ~3 s longer.
- Hypothesis (not measured per mechanism): the extra latency comes from the durable engine's polling (process
  observation every 0.5 s, queue dispatch, run loop waits on messages) and from systemd unit start/stop per attempt,
  against the legacy owner's in-process loop; for real tasks that last minutes it is a small constant, while one
  avoided agent attempt is worth minutes and ~1.3 M tokens on REQ-021 (T2.6's legacy average).
- Not covered by this benchmark: crashes of the runtime itself (the legacy owner runs in process here; durable crash
  recovery is proven separately in `test_durable_e2e`), manual checks, subplans and audits (each has its own e2e:
  `test_durable_subplans`, `test_durable_attestations`, `test_durable_audits`).

## Rerun on the integrated code

Branch `req030-item4` at `8ec880bce` (iteration 2 merged: subplans, legacy-equivalent briefs, attestations, M2 router,
shell file guard, task pause, milestone audits). Raw results: `bench-runtimes/merged.{compare,legacy,durable}.json`.

| Metric | Legacy | Durable |
|---|---|---|
| Agent launches | 12 | 10 |
| Redundant launches | 2 | 0 |
| Owner interventions | 2 | 1 |
| Fixable tasks completed | 4 of 5 | 5 of 5 |
| Tokens | 1,440 | 1,200 |
| Recovery T2 / T3 / T4, s | 1.7 / never / 4.7 | 4.3 / 3.1 / 5.3 |
| Wall time, s | 9.0 | 28.8 |

The counts are unchanged by iteration 2 (the bench plan has no subplans, manual checks or audits, and the M2 router
picks the one allowed route); the durable wall time stays about 3× the legacy one on this plan.
