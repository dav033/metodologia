# REQ-020 contract and ownership freeze

Status: frozen for independent M2 and M5 module work on 2026-10-15. The source authority is REQ-020/SPEC and David's approved `SOURCE-PLAN.md`; M5's existing authority is REQ-019/SPEC and D-041.

## Public boundaries

| Boundary | Frozen contract | Owner |
|---|---|---|
| M1 ↔ M2 | Existing `AssignmentPort.propose(AssignmentRequest) -> Sequence[Assignment]`, approved `plan_sha256`, READY tasks and global `free_slots`; M1 validates every proposal. No new M1 retry field is required for baseline quota rerouting. | M1 integrator |
| M2 internal public API | Preserve per-task `DecisionRequest`/`DecisionRecord`; evolve M2 schema additively to 1.2.0 for quota windows, performance snapshot metadata and batch identity. Read legacy decision records 1.0.0 and 1.1.0. Add a bounded batch planner above the per-task API. | M2 |
| M1 ↔ M5 | Preserve M5 D-041 `RecoveryPort`, `FailureContext`, `RecoveryProposal` and M1 authority. M5 returns retry/wait/block plus advisory rationale; M1 verifies termination and authorizes any retry. | M5 module; M1 integrator for shared wiring |
| M1 retry → M2 | M1 requests a fresh assignment after an approved retry; M2 re-reads current cached quota and normal eligibility. No RPC/import from M5 to M2. Route-avoid/retry context is unsupported unless M1 adds a separately approved, versioned field; no hint is inferred from free text. | M1 integrator |
| M2 ↔ M4/M6 | Optional validated observation inputs only. M2 package stays importable and deterministic when these modules or quality verdicts are absent. | M2 adapter owner |

## Data invariants

- Effective provider account is represented by an opaque `account_ref`; aliases do not multiply quota.
- Preserve each provider- and model-scoped window independently. All relevant fresh windows must permit selection; an imminent short reset cannot override an exhausted weekly/model window.
- Use cached observations only. `observed_at <= now < valid_until` is necessary for fresh evidence. Missing reset metadata remains unknown unless that source explicitly permits an unknown reset while the observation TTL is still fresh.
- M2 1.2.0 quota demand keeps provider-reported tokens and quota percentage points as separate units. Attribute account-window deltas only for one known active task, a known unchanged reset, and explicit evidence that no external usage occurred; otherwise return `attribution_unknown`. Estimates match exact account/route/context/source/unit, expose sample count and empirical bounds, and carry a bounded TTL without claiming calibrated confidence.
- Never convert usage percentages to tokens or dollars. Quota deltas are assigned to a task only with comparable before/after observations and no concurrent external use or reset; otherwise attribution is unknown.
- A verified outcome requires the independent acceptance evidence and matching plan/revision/task/attempt/decision/route identities. Claims and uncorrelated historical rows are not positive training labels.
- M2 may make temporary calculations for one batch but cannot reserve capacity durably or change M1/M3 state.

## File ownership

| Files / area | M2 | M5 | Single integrator |
|---|---|---|---|
| `skill/scripts/bt_scheduler_decision/**` | Write | Read only | No concurrent edits |
| `skill/scripts/bt_scheduler_decision_adapter.py` | Write | Read only | No concurrent edits |
| `skill/scripts/bt_scheduler_recovery/**` | Read only | Write | No concurrent edits |
| `skill/scripts/bt_scheduler_recovery_adapter.py` | Read only | Write | No concurrent edits |
| `bt_scheduler_core/**`, `bt_scheduler_adapter.py`, `bt_scheduler_executor_adapter.py`, shared schemas, M4 wiring, `pyproject.toml` | Propose only | Propose only | Write once after both module contracts pass |
| M2/M5 package tests | Own suite | Own suite | No cross-edits |
| M1–M5 E2E, shared packaging tests and shared requirement log/decision files | No concurrent edits | No concurrent edits | Integrator |

M2 implementation lives in `/home/david/dev/metodologia-m2` on `feat/scheduler-m2-learning-quota`. M5 implementation lives in `/home/david/dev/metodologia-m5` on `feat/scheduler-m5-recovery-manager`; its isolated package baseline passed 33 tests before implementation started. Existing dirty M4/M5 files in the primary worktree remain preserved. No shared files are to be copied or merged early.

## Integration gates

- P0: inventories, this ownership matrix and module contracts are frozen before parallel implementation.
- P1: isolated M2 and M5 unit/contract suites pass without importing the sibling module.
- P2: one integrator applies only necessary shared wiring, preserving M1 ownership and M3 compatibility.
- P3: fake-backed M1/M2/M3/M5 E2E covers exhausted A → eligible B, no capacity, duplicate/tardy evidence and wait/block.
- P4: accepted metrics use real correlated verification; unknown/ambiguous usage remains explicitly uncovered.

## Experiment gate

The real-provider experiment is not part of offline tests. Do not start provider agents or consume subscription quota until David explicitly authorizes the bounded run (8–12 tasks, 2–3 agents, 2–4 hours at most, controlled failures without intentional exhaustion). A missing authorization leaves T24 and dependent closeout evidence pending.
