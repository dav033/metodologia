# REQ-029 — recovery boundary, migration and rollback

Purpose of this directory: the review artifacts of the recovery work (checks reports, audit ledgers, previews). This file is the
rollout document of REQ-029 for the owner; the canonical decision is D-116..D-120 plus the REQ-029 entry the owner publishes.

## Why it is built this way
- **Authority.** M1 alone changes task and attempt state. Recovery produces *advice and plan revisions*: M5 stores cases
  (`recovery-case/1`, `recovery-proposal/1`, `recovery-progress/1`), the methodology layer collects evidence (`bt_recovery_evidence`),
  compiles a constrained revision (`bt_recovery_compiler`, `bt_recovery_convergence`), authorizes it once per cycle
  (`bt_recovery_authorization`) and applies it through ONE generic M1 primitive (`bt_recovery_apply` -> `apply_plan_revision`),
  journaled so a crash adopts the same revision and never applies a second one.
- **Bounded.** One recovery cycle per run and audit/conflict lineage, at most one diagnosis and eight corrective implementation tasks,
  ordinary attempts, reworks and `budget_base` untouched. A cycle that finds no permitted strategy ends in a durable blocker.
  An unchanged conflict (same snapshots, paths, merge base, carry) is the same case whatever the plan revision.
- **Evidence before action.** Conflict observations are published complete before any clipping (`conflict-observation/1`); a missing
  source is `evidence_unavailable`, never an empty success. Only independent verification and audit evidence on the resulting
  integrated tree closes a case.
- **The scheduler's own recovery (REQ-030).** `bt_scheduler_healing` handles the common stops (transient, quota, clash, mapping,
  regression, plan defect) with the smallest safe repair and records them in `RUN.interventions.jsonl`; this recovery is the
  structural path for what it leaves.

## Versions and migration
Contracts: `conflict-observation/1`, `conflict-strategy/1`, `convergence-work/1`, `recovery-verification-map/1`,
`recovery-authorization/1`, `recovery-apply/1` (journal). The M5 `/1` case/store records stay readable; the structural envelopes are
separate and additive. Existing runs keep their legacy decision cards and audit records. A migrated store is never restored from a
backup automatically.

## Operation
- `scheduler-op REQ recovery-preview` (read-only: hashes, lineage, uncertain matches, blockers, no diagnostic model) and
  `recovery-status`; the plan page shows the recovery and self-healing state with a stop control; `scheduler-op REQ heal stop|revert`.
- Preview of the REQ-027 history runs on disposable stores built from the sanitized fixture; it never touches the live run.

## Rollback
1. Stop recovery (`heal stop`, or hold the run). 2. Keep the journal, evidence and accepted snapshots as they are.
3. Disable diagnostic recovery on the same tested runtime (the default for runs that did not opt in). 4. Never downgrade the binary,
restore a migrated store or reset a counter; an older runtime is allowed only with explicit capability evidence that it reads the
current schemas without loss, followed by the normal owner workflow.

## Rollout status (2026-10-22)
The conditional activation on REQ-027 (R9) is **withdrawn**: REQ-027 completed 46/46 and was merged (a5854d5f6). `bt_recovery_rollout`
(pinned staging of the accepted tree) stays as accepted code and is not used by any run. Other existing runs need their own authorization.
