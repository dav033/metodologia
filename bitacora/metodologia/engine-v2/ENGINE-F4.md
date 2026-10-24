# Engine v2 F4 — git engine and M1–M6 (design)

Lead: session `59ae629e`, 2026-10-23. Authority: CONTRACT §2 F4, §6; master §2–3, §12.2, §13.6, §14.3, §15.2–15.9;
schema `SCHEMA-1.3.0.md`. Decisions D-07..D-10 of the master are resolved here.

## 0. Invariants

1. Legacy runs and plans (< 1.3.0, or 1.3.0 without `subplans`) behave exactly as before: same states, same refs, same
   integration line, same verdict fields. Every new behaviour is keyed on a 1.3.0 plan **with subplans**.
2. Module rules (`modules.md`) hold: new logic in an isolated package with ports; git/subprocess only in adapters.
3. Git is evidence of text, never of compatibility. Compatibility = contract + tests on real implementations.
4. A published composition is never rewritten. A failed candidate leaves the previous composition intact.
5. No action on graph ancestry alone. A changed producer triggers at most `reverify` of a consumer until an executed
   check demonstrates incompatibility.
6. A missing credential/environment never consumes code retries and is never `FAIL` or `PASS`.

## 1. `bt_composition` (new isolated module) + `bt_composition_adapter.py`

Pure logic over two ports: `GitPort` (objects-only operations: `rev_parse`, `merge_tree(base, ours, theirs)`,
`commit_tree`, `update_refs(transaction: [(ref, new, expected_old)])` atomic CAS, `tree_digest(commit, paths)`,
`diff_paths(a, b)`, `add_worktree/remove_worktree` for candidate workspaces) and a `Store` (SQLite WAL inside the
module, file path passed in: `<bitácora root>/.state/composition/<project>-<REQ>.db`).

- **Subplan version** `SP@vN`: immutable ref `refs/subplans/<plan>/<SP>/v<N>` (create-only CAS from zero) to the
  subplan's line tip at acceptance; record `{plan_id, plan_revision, subplan_id, version, commit, line_base,
  contracts: {contract@major: sha256 of its design/contract doc or "declared"}, evidence: [{task_id, kind, verdict_id,
  tree_digest, environment}], published_at}` with `manifest_sha256`. N increments per publication.
- **Composition** `C<N> = {SP@vX…}`: record `{id, parent: C<N-1>|null, members, base_commit, integrated_commit,
  manifest_sha256, state: candidate|verifying|published|rejected, verdicts}`. Refs:
  `refs/compositions/<plan>/candidates/C<N>`; on publish `refs/compositions/<plan>/C<N>` and
  `refs/compositions/<plan>/current` CAS `C<N-1> → C<N>` in **one** `update-ref --stdin` transaction.
- **Candidate build**: start from `current` (or the run base); for each changed member fold its own delta
  (`line_base → version commit`, `merge-tree --merge-base`) in plan order; objects only. A textual conflict ends the
  candidate `rejected` with class `git_text_conflict` and the paths; `current` untouched.
- **Candidate workspace**: a temporary worktree of the candidate commit for the composition gate's commands; removed
  after the verdict (kept on failure only as a snapshot ref, never as a folder).
- **Publish on pass only** (the composition gate task's M6 PASS + its audit if declared); otherwise `rejected` with
  the verdict evidence.
- **Selective propagation** `propagate(change, consumers, evidence) -> [Action]` with distinct operations
  `reverify | reintegrate | audit | adapt_contract | modify | reimplement`:
  - internal change (no produced contract hash changed) → nothing for consumers (their evidence is rebound only if
    the equivalence proof below holds, else `reverify`);
  - contract hash changed, consumer tests not yet run on the new producer → `reverify` (+ `audit` if the public
    surface changed);
  - git conflict building the candidate → `reintegrate`;
  - executed consumer contract test FAIL_CODE against the new producer → `adapt_contract` (the producer broke its
    declared major) or `modify` (consumer must adapt to a new declared major);
  - `reimplement` only when a reviewer/M6 finding demonstrates the consumer design cannot meet the new contract;
    never produced automatically from ancestry.
- **Evidence binding**: `EvidenceKey = (tree_digest of the task's relevant paths, contract hashes it consumed,
  environment fingerprint)`. Reuse across versions only when the key is equal (equivalence proof = equal digest of
  the declared relevant paths + equal contract hashes + equal environment); otherwise `reverify`.

## 2. Result taxonomy (M6 evidence, M5 policy)

Compatible evidence field `reason_code` on M6 verdict evidence (and Runner notes):
`PASS | FAIL_CODE | BLOCKED_EXTERNAL | BLOCKED_ENV | TIMEOUT | FLAKY_SUSPECTED | NOT_RUN`. Verdict values
(`PASS/FAIL/NEEDS_REVIEW`) do not change. Migration: records without it read as `UNCLASSIFIED`; the evidence schema
gets a minor version; old stores load. Classification sources: missing declared `requires` names / sandbox refusal →
`BLOCKED_EXTERNAL`/`BLOCKED_ENV`; command timeout → `TIMEOUT`; nonzero with assertion → `FAIL_CODE`; PASS after FAIL
on the same key → `FLAKY_SUSPECTED`; not executed → `NOT_RUN`. M5: `BLOCKED_*` → hold/wait with an owner/environment
notice, **no attempt budget consumed**; `TIMEOUT` → one retry then block; `FLAKY_SUSPECTED` → never accepted on a single
PASS (re-run policy owned by M6 config); `FAIL_CODE` → normal retry/rework.

## 3. Module changes

- **M1 core** (`bt_scheduler_core`): `PLAN_SCHEMA_CAPABILITIES` adds 1.3.0; plan model exposes subplans and gates
  (read-only); derived views `subplan_status` (`open | auditing | accepted | published`) and composition records
  mirrored from adapter facts through audited operations `subplan_version_published`, `composition_candidate`,
  `composition_published`, `composition_rejected` (observations; tasks still change state only through existing
  transitions). Gate: a composition gate task is dispatchable only when every member subplan has a published version
  (an adapter-provided fact checked in the core's readiness via an injected predicate/port, default allow for legacy).
- **M2 decision**: route `kind: design` to role `designer`; an audit task named as a subplan's
  `visual_review_task` to role `reviewer` with axis `visual`; spec/standards unchanged.
- **M3 executor**: per-subplan lines `refs/m3/line/<run>/<role>/<SP>` that fold the subplan's accepted tasks and
  their accepted ancestors only (never another subplan's unaccepted or unrelated work); tasks without subplan in a
  subplan plan (gates, final acceptance) start from the composition candidate/current commit. Workspace kinds:
  `attempt` (exists), `subplan` (reconstructable from the line ref), `integration` (candidate). Designer write scope
  (F2-E) stays. Designer-contract gate: a `ui: true` task does not start unless `design/contracts/<id>@v<N>.md`
  exists in its base tree (`DESIGN_CONTRACT_MISSING`, a blocked-environment class, not a code failure).
- **M5 recovery**: policy by `reason_code` (§2); localized rework from `propagate()` — only the demonstrated frontier.
- **M6 quality**: findings schema `audit-findings/1` gains optional `semantic_fingerprint` (contract_id +
  failure_mechanism + trigger + affected_frontier, normalised, sha256); the gate deduplicates open findings by it
  (independent evidence merged, distinct defects on the same line not merged); composition verdicts carry
  `composition_id` + `manifest_sha256` and bind evidence to the candidate tree.
- **Review policy** (`bt_review_policy.py`): a task of a subplan whose `audit_task` is pending is covered (no
  per-commit antagonist), like a pending milestone audit.

## 4. Benchmark D-10

Replay through the real M1 core with simulated M2–M6 (`bt_scheduler_core.simulators`): the P-177 fixture plan in
its 1.2.0 shape (old flow) and 1.3.0 shape (new flow), each with and without injected defects F1–F5 (a defect makes
the first barrier that observes it reject and name the introducing task). Measure redone tasks, accepted minutes
discarded (sum of `estimated_minutes` of accepted tasks reset), token proxy (attempt minutes × a fixed rate),
simulated wall time at parallel 3. `bt_recovery_benchmark` must not get worse. Results go to the bitácora.

## 5. Ownership and order

| Task | Owns | After |
|---|---|---|
| F4-1 composition module | `bt_composition/**`, `bt_composition_adapter.py`, tests | F1-A |
| F4-3 M1 | `bt_scheduler_core/**`, `bt_scheduler_adapter.py` (capability + facts) | F1-A |
| F4-4 M2 | `bt_scheduler_decision/**`, `bt_scheduler_decision_adapter.py`, role catalogue | F1-A, F2-D |
| F4-6 M6 + taxonomy | `bt_scheduler_quality/**`, `bt_scheduler_quality_adapter.py`, `bt_audit_gate.py` | F1-A |
| F4-2 M5 | `bt_scheduler_recovery/**`, `bt_scheduler_recovery_adapter.py` | F4-6 |
| F4-5 M3 | `bt_integration_line.py`, `bt_scheduler_integrator.py`, `bt_scheduler_executor*` | F4-1, F2-E |
| F4-7 policy + switch | `bt_review_policy.py`, `bt_plan_adapter.py`, planner `SCHEMA_VERSION` default | F4-3..6 |
| F4-9 owner wiring | `bt_scheduler_run.py`, `bt_scheduler_executor_wiring.py` | all above |
| F4-8 benchmark | `bt_engine_benchmark*`, fixtures | F4-9 |

## 6. Data-flow contracts fixed during F4 (lead rulings)

- M1 → M2/M3 task metadata (1.3.0 with subplans, optional keys): `subplan_id`; `review_axis: "visual"` for a subplan's
  `ui.visual_review_task`; `ui: true|false` when declared. M2 maps `kind: design` → role `designer` and
  `review_axis: visual` → role `reviewer` (axis visual) in `bt_role_policy.py`. M3 derives the brief's axis from the
  frozen plan itself.
