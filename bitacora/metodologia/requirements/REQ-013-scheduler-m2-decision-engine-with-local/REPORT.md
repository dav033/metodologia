---
req: REQ-013
status: delivered-uncommitted
date: 2026-10-14
---
# Report — REQ-013 — Scheduler M2 Decision Engine with local Laya

## Outcome

M2 is implemented as the isolated, standard-library-only package `skill/scripts/bt_scheduler_decision/`, reached
through `bt_scheduler_decision_adapter.py` and the additive M1 assignment contract. It filters invalid candidates
deterministically, ranks the survivors against the existing router reference and verified local history, optionally
asks the bounded local Laya worker to compare eligible routes, and persists a redacted, replayable decision. M1 still
validates every proposal and owns task state, global slot limits, resource claims and atomic reservations.

Laya is installed, offline-ready and measured on the RTX A3000. Its inference path selected CUDA in measured runs.
The quality gate intentionally keeps recommendations deterministic: no checkpoint supplied a confidence score that
passed calibration, and the held-out Laya selection scored below the deterministic reference. This is the approved
failure behavior, not evidence that Laya improved routing. `approved_evidence_sha256` is empty, so locally fabricated
or edited benchmark files cannot activate it; a future activation requires new passing evidence and an explicit
code-reviewed digest entry.

## Implementation

- Reused `bt_agents` for the existing model/provider/account inventory and baseline ordering; `bt_profiles` for profile
  authorization; `bt_subscriptions` for quota state and freshness; and existing telemetry for verified outcomes,
  duration and token history. Unknown or stale quota, invalid auth, unavailable capacity, cooldown and exhausted quota
  are hard exclusions. Account identifiers are SHA-256 aliases; credentials, environment, prompts and raw model output
  are not persisted.
- Added an additive Scheduler contract v1.1.0 transport for the approved plan hash, dependencies, acceptance,
  verification and Planner classification evidence. `DecisionAssignmentPort` supplies M2's opaque selected-route
  reference; M1 remains the sole authorization and reservation authority.
- Added stable candidate eligibility and ranking, conservative sparse-history scoring, typed validation, a private
  bounded SQLite ledger with exact replay and snapshot linkage, read-only selected-route resolution, and deterministic
  fallback for missing/unreliable Laya.
- Installed Laya 0.4.7 at pinned source commit `432312b36714d8889eba405507b37eda25257d9c` in
  `~/.local/share/bt-scheduler-laya`, with Python 3.12.14 and PyTorch `2.14.0+cu132`. Three official checkpoints are
  pinned by revision, size and SHA-256 in the installer. The worker prefers CUDA and falls back to CPU; it keeps one
  checkpoint resident, enforces a deadline/circuit breaker and runs under a systemd cgroup with 5 GiB memory and no
  swap. `HF_HUB_OFFLINE=1 ... setup_bt_scheduler_laya.py --check` succeeds without network access.
- Packaged `bt_scheduler_decision`, its API contract, README and Laya dependency lock in the wheel; an installed-wheel
  test imports M2 under `python -I` outside the source checkout.

## Measured Laya behavior

Hardware: NVIDIA RTX A3000 Laptop GPU, 6,141,509,632 reported VRAM bytes, compute capability 8.6; CUDA 13.2. All
three official checkpoints completed 100 CUDA calibration choices apiece over the frozen English/Spanish fixture
split (150 cases per language across the three models), with 100 valid choices and no truncations per model.

| Checkpoint | Cold first choice | Warm median | Warm p95 | Peak RSS | CUDA inference allocation |
|---|---:|---:|---:|---:|---:|
| English | 7.377 s | 77.883 ms | 79.644 ms | 3.540 GB | 2.448 GB |
| Multilingual | 10.580 s | 41.376 ms | 42.897 ms | 3.047 GB | 1.600 GB |
| Typed decisions | 7.682 s | 78.082 ms | 79.651 ms | 3.539 GB | 2.448 GB |

The typed-decisions held-out benchmark used 100 cases across five families. Peak CUDA reserved memory was 2.682 GB;
peak RSS was 3.541 GB under the 5 GiB/no-swap limit. CPU fallback was exercised for one real local inference per
checkpoint; CPU RSS ranged from 2.899 to 3.395 GB and CUDA allocation was zero. CPU results are runtime smoke tests,
not a CPU quality benchmark.

The measured held-out raw Laya choice accuracy was 14/100 versus 21/100 for the deterministic reference. The paired
raw delta's fixed-seed 95% bootstrap interval was `[-0.18, 0.04]`; mean regret was 0.11443 for Laya versus 0.09348
for the reference (lower is better). No checkpoint had a usable calibrated confidence cutoff (`retained=0`,
`cutoff=null`). The production hybrid therefore used the deterministic reference on all 100 cases: 21/100 accuracy,
paired interval `[0.0, 0.0]`, zero hard-filter violations, zero truncations. Fixture labels are synthetic algorithmic
utility labels, not human or production task-success outcomes.

## Verification

| Scope | Command | Result |
|---|---|---|
| M2 module | `cd skill/scripts && PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s bt_scheduler_decision/tests` | 64 passed |
| Planner | `cd skill/scripts && PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s bt_planner/tests` | 199 passed |
| M1 core | `cd skill/scripts && PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s bt_scheduler_core/tests` | 239 passed |
| Planner/M1/M2 integration | `PYTHONPATH=. python -W error::ResourceWarning -m unittest tests.test_plan_integration tests.test_scheduler_integration tests.test_scheduler_decision_sources tests.test_scheduler_decision_contract` | 89 passed; includes Plan check/freeze → M1 SchedulerCore → persisted M2 decision → M1 reservation and route resolution |
| Focused M2 adapters/benchmark/worker | `PYTHONPATH=. python -W error::ResourceWarning -m unittest tests.test_scheduler_decision_sources tests.test_scheduler_decision_contract tests.test_scheduler_benchmark tests.test_scheduler_bench_quality tests.test_scheduler_laya_worker` | 37 passed |
| Full methodology | `PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s tests` | 916 passed, 3 skipped, exit 0 |
| Installed package | `python -W error::ResourceWarning -m unittest discover -s tests/migration -p 'test_package_install.py'` | 13 passed, including M2 wheel contents and isolated import |
| Static checks | Scoped Ruff, `py_compile`, API-contract JSON parse, `git diff --check` | Passed |
| Offline runtime | `HF_HUB_OFFLINE=1 python skill/scripts/setup_bt_scheduler_laya.py --check` | Passed; pinned Laya, Torch, CUDA and all checkpoint hashes verified |

Two independent final reviews (spec and standards) approved with no findings. The standards review reproduced rejection
of synthetic benchmark artifacts and verified the M2 wheel plus Plan→M1→M2 route persistence. Earlier audit findings
for self-authorizing synthetic evidence and omitted wheel package data were fixed with regression tests.

The full methodology run printed an ignored `subprocess.Popen.__del__` `ResourceWarning` after its 916-test OK summary;
the reported child PID was already absent during follow-up inspection. The focused M2, Planner, M1, integration and
package suites all ran with `ResourceWarning` promoted to errors and passed. No source of the unrelated full-suite
warning was established.

## Limits and release state

- M2 is integrated through the M1 contract and is exercised end to end, but no production run was deployed. M1
  continues to decide whether to reserve a recommendation.
- Laya is proven to run on the GPU for local measurement, but is not authorized for live route recommendations because
  the actual frozen benchmark did not establish improvement or a usable confidence cutoff. It is not silently enabled.
- CPU fallback is verified for local execution; only CUDA received the 100-case quality benchmark.
- No paid decision API was used for M2 selection; one owner-authorized Antigravity subscription run exercised M3.
  No external deployment, commit, push or historical execution rewrite occurred. Concurrent REQ-014 files were preserved.

## Current closeout verification — 2026-10-15

After later Scheduler edits, the M2 package passed 65/65 tests, M1 core passed 244/244, Planner passed 219/219, and
the Plan → M1 → M2 integration suite (including the existing full-chain fixture) passed 78/78 with
`ResourceWarning` promoted to errors. Scoped Ruff, Python compilation, API-contract JSON parsing and `git diff
--check` passed. Ruff identified two ordering-only findings in M2's public export list; they were sorted and all M2
and integration suites passed again.

The installed-package suite currently reports 12/13: its only failure,
`test_py_modules_cover_every_runtime_script_and_nothing_else`, detects the two in-progress M4 adapters
`bt_scheduler_monitor_adapter` and `bt_scheduler_stream_adapter` missing from the packaging module list. This is a
workspace-wide packaging issue outside REQ-013; the M2 wheel-content and isolated-import checks passed. No M4 source
or packaging configuration was changed as part of M2 closeout. The stale test name `test_scheduler_decision_integration`
in the original verification table is absent from the current tree; the extant integration modules were run directly.

M2 remains complete in its guarded mode: hard filters, quota/profile rules, persisted recommendations and M1
authorization pass; live recommendations remain deterministic because the frozen Laya route benchmark was 14/100
versus 21/100 for the reference and no confidence cutoff qualified. The isolated real-provider smoke below adds
live M3 evidence without enabling Laya.

## Real provider end-to-end smoke — 2026-10-15

The disposable project at `/home/david/.local/share/bt-scheduler-real-e2e/20261015T191914Z-run2` ran the actual
Planner `init → check → freeze`, M1 `SchedulerCore`, M2 methodology `DecisionAssignmentPort` and decision ledger, and
M3 `MethodologyDriver`/Antigravity CLI. M1 reserved the exact M2 ledger reference; M3 resolved it to
`antigravity / gemini-3.8-flash-low` and completed one attempt (exit 0, terminal result seen, handoff snapshot
`7c88fbfa18c282adad2eaa8df1a36402bb5995fc`). The independent verifier ran five standard-library unit tests, all
passing; M1 alone completed the task. End-to-end wall time was 86.4 s. The source checkout remained at its initial
HEAD with an empty worktree; all agent edits and the snapshot commit stayed in the disposable M3 worktree.

At selection time Antigravity had fresh verified quota at 39%; a post-run usage read reported 40% weekly and 1% in the
five-hour window, with no exhaustion. Claude Haiku and both Codex profiles were excluded as `auth_unknown` and
`quota_stale`, so this live run proves one real eligible route through the complete chain, not a choice between
multiple live-eligible providers. M2 used the deterministic method; Laya was not invoked. The provider reported
160,668 total tokens; `cost_usd` was null and is not interpreted as zero cost. No paid API was used for the decision.

An audit found a harness/spec gap: the scratch SPEC requested a dedicated Unicode/apostrophe unit test, but the frozen
plan acceptance did not include that case and the agent omitted such a test. A separate read-only probe confirmed
`greet("  María O'Neil  ")` returns `Hello, María O'Neil!`; this does not replace the missing unit-test coverage.
Artifacts include `result.json` and `post-run-audit.json` alongside the isolated Planner, M1, M2 and M3 ledgers. P-036
tracks a second real-route smoke for a time when at least two profiles have fresh verified quota.

The first runner process returned exit 1 because two of its summary assertions assumed an M3 `outcome.status` field and
passed M1's `route:` wrapper directly to the public M2 binding lookup. A separate read-only audit corrected those
interpretations against the persisted ledgers, re-ran the unit tests, and exited 0; no provider was invoked again.

## Quota verifier audit — 2026-10-15

The audit followed cached provider metadata through M2's hard filters, the M2 decision ledger, and M3's route
resolution/launch checks. It found and fixed four fail-open or crash gaps: Codex denial fields were not honored (the
official schema places `spendControlReached` and `rateLimitReachedType` in each bucket); model-scoped Codex buckets
were not applied to the matching model; Antigravity accepted malformed numeric cache types; and very large numeric
observations could raise instead of becoming unknown. M2 now persists quota observation, usage and
expiry on each eligible route; M3 rejects missing, malformed, or expired single-use evidence at resolution and again
before launch. Legacy M2 1.0.0 decisions remain readable but cannot launch without that evidence.

| Scope | Command | Result |
|---|---|---|
| Quota parsing, M2 source bridge, M2→M3 route contract, executor route model | `PYTHONPATH=.:tests python -W error::ResourceWarning -m unittest tests.test_subscription_usage tests.test_agy tests.test_scheduler_decision_sources tests.test_scheduler_route_resolution tests.test_scheduler_executor_adapter bt_scheduler_decision.tests.test_recorder bt_scheduler_executor.tests.test_contracts` | 149 passed |
| M2 package tests excluding the currently failing boundary audit | `PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s bt_scheduler_decision/tests -p 'test_[!b]*.py'` | 66 passed |
| M3 executor module | `PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s bt_scheduler_executor/tests` | 276 passed |
| Planner, M1 core and Plan/M1 integration | Planner discovery; M1 core discovery; `tests.test_scheduler_integration tests.test_plan_integration` | 219 + 248 + 49 passed |
| Changed quota/runtime modules | Scoped Ruff `E4,E7,E9,F`, `py_compile`, API-contract JSON parse, `git diff --check` | Passed |

The full Ruff run over the touched file set still exits 1 with 39 style diagnostics, mainly in older code and the
concurrent M4 adapter/test edits. No new quota-path finding appeared in the focused `E4,E7,E9,F` check; the touched
quota implementation modules passed it.

The complete M2 discovery currently has one independent failure: the in-progress M4 file
`bt_scheduler_decision/tests/test_metric_history.py` imports `bt_scheduler_decision_adapter`, violating M2's package
boundary test. That shared M4 work was left untouched. An offline inspection of existing local caches found one fresh
Antigravity sample (40% used), while both Claude and both Codex profile samples were stale/unknown; this agrees with
the existing real smoke, which had only one eligible route. No usage refresh, agent launch, model inference, paid API,
or historical execution was performed during this quota audit. The two-hour quota window cannot lock a provider's
remote quota: service-side usage can still change after a valid local sample.

### Follow-up: Claude null reset and M2 eligibility (2026-10-15)

The Claude parser now accepts an explicit `resets_at: null` while continuing to reject a missing reset field,
malformed timestamps and invalid utilization. M2 keeps the null-reset window active only while its quota sample is
fresh, uses the measured utilization for ranking, and blocks a fresh 100% sample as exhausted even without a reset
timestamp. Codex reset timestamps remain required. A synthetic 0% five-hour / 96% weekly Claude sample was eligible
through M2's candidate ranking; a malformed null-reset Codex sample remained unknown.

Verification after the fix:

- `PYTHONPATH=skill/scripts/tests:skill/scripts python -W error::ResourceWarning -m unittest test_subscription_usage test_scheduler_decision_sources` — 34 passed.
- `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest discover -s skill/scripts/bt_scheduler_decision/tests -p 'test_[!b]*.py'` — 66 passed, excluding the boundary audit.
- Focused Ruff `E4,E7,E9,F`, `py_compile` and `git diff --check` passed.

The full Ruff command over the edited subscription test still reports three `E701` findings already present at HEAD;
the changed test file passes when those baseline findings are excluded. Before the refresh, the local cache had Claude
rows `invalid_response` and 16,110–19,711 seconds old, Codex rows `app_server_unavailable` and 156,454–156,455
seconds old, and one fresh Antigravity row at 40% used (3,991 seconds old).

After the tests passed, one bounded, read-only Claude usage request returned 0% five-hour usage with
`resets_at: null` and 96% weekly usage. The sample was injected into the in-memory M2 candidate source alongside the
still-fresh Antigravity cache: both were eligible and M2 ranked `claude-personal` first. The sample was not written
to the quota cache; no M2 decision was persisted and no M3 agent was launched. P-036 remains open for the full
persisted Planner/M1/M2/M3 smoke, which must recheck fresh quota immediately before execution and awaits owner
approval for another subscription-backed agent launch.
