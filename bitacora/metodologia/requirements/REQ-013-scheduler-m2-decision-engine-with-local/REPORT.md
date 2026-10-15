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
- No paid decision APIs, external deployment, commit, push or historical execution rewrite was performed. Concurrent
  REQ-014 files were preserved.
