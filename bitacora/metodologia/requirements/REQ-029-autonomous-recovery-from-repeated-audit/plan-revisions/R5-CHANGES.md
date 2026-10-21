# REQ-029 revision 5 candidate: M1 without recovery logic

Draft only. Built from frozen `PLAN.r4.json` into `PLAN.r5.candidate.json` (revision 5, 35 tasks; r4 had 33).
Nothing is frozen or approved, and nothing was rebased. `PLAN.json` and `PLAN.md` are unchanged.

Owner decision applied: M1 (`skill/scripts/bt_scheduler_core/`) exposes one generic primitive. It applies a plan
revision atomically and idempotently when the source, accepted-map and base digests and the stop generation still
match. It preserves ordinary budgets, waits, reworks, attempts and unrelated accepted work. The state schema change
is additive, and schema 1/2 readers stay. Everything specific to recovery moves to methodology modules.

## Moved out of M1

| Concept (r4 T4, in M1) | r5 owner |
|---|---|
| recovery-authorization/1, scoped task grants, unique consumption keys | `bt_recovery_authorization.py` (T4c), own SQLite ledger `RUN.recovery-authorization.db` |
| One supplementary audit attempt per audit | T4c ledger (one consumption per audit lineage and cycle) + T5 RecoveryAdapter answers `block` for further retries. M1 grants no extra attempts. Observed: `reservation.claim` never checks the remaining budget and `recovery.apply_recovery` blocks after a failure once the budget is spent, so a reset exhausted task gets exactly one more dispatch. |
| conflict-bootstrap/1 grant | T4c ledger `consume_bootstrap`, called only by the existing M3 base_ref callable (wired in T5) |
| Compiler, verification map, oracle red/green, additive repair_verification | `bt_recovery_compiler.py` (T4b), pure |
| Crash-window journal (prepared/frozen/applied/rebound/committed), owner-hold check, rebind | `bt_recovery_apply.py` (T4c), reusing `bt_scheduler_ops.hold`, the stop-owner move and `bt_scheduler_run.rebind_runtime` |
| "M1 accepted convergence mapping" | dropped: C is accepted through ordinary M1 acceptance under the revised DAG. The T4c receipt records the lineage, and a fresh PredecessorIntegrator after rebind drops the stale memo |
| `bt_scheduler_core/diagnostic_recovery.py`, `tests/test_diagnostic_recovery.py` | not created |
| `bt_scheduler_core/recovery.py` | unchanged (attempt-level retry/wait/block, unrelated) |

M1 files that remain, all generic: `rebase.py` (new `apply_plan_revision`, `RevisionGuard`, `RevisionApplication`,
`accepted_map_digest`, `stop_generation`; `rebase_run` unchanged), `model.py` (schema 3: `revision_barrier`,
`revision_applications`; reads 1/2), `__init__.py` (exports), `README.md` (`test_readme` checks `__all__`).
These two files also stay, with a justification:
- `reservation.py`: claims are refused with `revision_pending` while an unexpired barrier exists. Without this,
  continuous new dispatch could starve the quiescent apply (R15). A barrier is bounded by `Config.max_recovery_wait`,
  and an expired barrier stops blocking with no write.
- `operations.py`: `pause` and `cancel` increment `counters['stop']`. M1 had no stop generation, so a
  pause→resume between guard capture and apply was invisible (finding F3).

`bt_flow_bus.py` gains M1_RULES for `revision_barrier` and `revision_applied`, because `tests.test_flow_contract` requires
a rule for every M1 audit kind. T10 also writes this file later. The two tasks are ordered.

## Per task

- **T4** has a new title, objective, criteria and verification. It now holds the generic primitive only, with a full
  decision order. After: T3b. Covers R5, R6, R10, R15. The paths are the M1 files above plus
  `bt_scheduler_core/tests/test_revision_apply.py` and `bt_flow_bus.py`. Its checks are the functional test, an AST
  vocabulary boundary test, the `bt_scheduler_core/tests` suite and the project boundary guard. Classification:
  complexity medium (high in r4, because the decision order is now resolved in the plan), risk high, 90 min. Shared
  resource: `m1-run-state-schema` (new).
- **T4b** is new and holds the compiler outside M1 (`bt_recovery_compiler.py`, `bt_plan_adapter.validate_candidate`,
  `tests/test_recovery_compiler.py`). After: T3b. Covers R4, R5, R8, R10, R12, R13. Its checks are the functional test,
  `bt_planner/tests` and the boundary guard. 120 min.
- **T4c** is new and holds the authorization ledger and journaled application (`bt_recovery_authorization.py`,
  `bt_recovery_apply.py`, `bt_remediation.py`, `bt_scheduler_adapter.py`, `tests/test_recovery_authorization.py`,
  `tests/test_recovery_apply.py`). After: T4, T4b. Covers R4, R5, R6, R8, R9, R10, R13, R15. It keeps **r4 T4's
  acceptance criterion verbatim** with the same `test_recovery_apply.py` command (`created_by` is now T4c). Added
  checks: the ledger test, `test_remediation.py` (F2 journal-before-freeze) and the boundary guard. 140 min.
- Union of covers for T4, T4b and T4c: R4, R5, R6, R8, R9, R10, R12, R13, R15. This is the same set as r4 T4. No
  criterion or check was removed.
- **T4a**: after changed from T4 to T4c. Objective references updated (T4b compiles, T4c applies through T4's
  primitive, the bootstrap grant comes from the T4c ledger, no extra M1 mapping). Coupling evidence adds T4b and T4c.
- **T5**: objective text updated (barrier only through T4c, bootstrap through
  `bt_recovery_authorization.consume_bootstrap`, the supplementary audit enforced by the ledger plus RecoveryAdapter,
  the real M1 stop generation and accepted map read through the adapter and never a constant). Paths and `after` are
  unchanged.
- **T6a**: one sentence changed ("identity-bound M1 grant" becomes the T4c ledger grant fenced against M1 identities).
- **T8.1, T8.5**: `expected_paths` re-pointed to the r5 files (13 paths: T4 and T4c implementation files plus
  `bt_plan_adapter.py`; the moved files were dropped). Shared resources add `m1-run-state-schema`. Classification
  evidence adds `task:T4c`. A short "Revision 5 boundary" paragraph is appended to the objective. Finding text,
  criteria and verification are unchanged.
- **T8.2, T8.6, T8.8**: no change needed. Their paths are T5/T6a files, and their mentions are of
  `tick_diagnostic_recovery` and similar methodology names.
- **T8, T9, T14, T15, T18, T19**: the audit command `--tasks` lists gain `,T4b,T4c`. T8's objective adds a check that
  M1 carries only the generic primitive.
- **M1 milestone**: added the criterion "M1 gains only one generic atomic plan-revision primitive; the recovery logic
  lives outside it".
- **Interfaces**:
  - IF-4 is now *Recovery authorization ledger and journaled application /1*, with producer T4c.
  - New IF-11 is the generic M1 primitive (producer T4). New IF-12 is the compiler (producer T4b).
  - IF-9 and IF-10 texts were re-pointed to T4b/T4c and the ledger.
  - IF-1, IF-2, IF-7, IF-8 and IF-10 consumers changed from T4 to T4b/T4c.
- **T1, T2, T3, T3a, T3b**: untouched.

## PLAN.md lines the owner must add before freezing

`check` compares PLAN.md and PLAN.json. A synced copy is in the scratch directory:
`/tmp/claude-1000/-home-david-dev-metodologia--claude-worktrees-agent-acb708b1954bf77f6/fde4d41b-a32a-4556-9509-03ad18d4933a/scratchpad/root/metodologia/requirements/REQ-029-autonomous-recovery-from-repeated-audit/PLAN.md`.
The required edits:
1. Replace the T4 task line with the T4, T4b and T4c lines (title, `after`, `covers`, `kind` and the first verification
   command of each).
2. Set T4a to `after: T4c`.
3. Append `,T4b,T4c` to the six audit `verify:` commands.
4. Add the T8.1–T8.9 task lines and set T8 to `after: T7, T8.1 … T8.9`. This error already exists in r4: the
   remediation revisions never added these lines.
5. Update the *Single writing responsibilities* entry for T4 and add entries for T4b and T4c (prose, not checked).

## Validation

- Scratch root with the candidate as PLAN.json and the synced PLAN.md:
  `BITACORA_ROOT=<scratch>/root python3 skill/scripts/bitacora.py --project metodologia plan-json check REQ-029`
  exits 0 with `OK: PLAN.json is publishable`. All remaining warnings were already present in r4: T8.x guards and
  reused justifications, redundant `after` entries, `bt_scheduler_quality_adapter.py` declared by 4 tasks, and the T4a
  guard.
- `python3 -m bt_planner validate PLAN.r5.candidate.json` exits 0.
- `plan-json report`: every requirement is covered, `criteria_without_command` is empty, and there are no unordered
  conflicts or unconsumed results. Critical path: 3185 min; total: 3475 min (r4 T4 was 160 min, T4+T4b+T4c are 350 min).
- For comparison, the current r4 `PLAN.json` against the real PLAN.md is INVALID (10 errors, all from the missing T8.x
  lines).

## Residual risks

- SPEC §Convergence bootstrap still says "M1 grants only the named convergence order", and R15 says "M1 alone
  applies". The second holds through the primitive. The first contradicts the owner decision, so the owner should
  amend SPEC.md. The planner did not edit it.
- T3b (in progress) keeps its text "permitted only for the M1-granted convergence task". It was not edited so that T3b
  stays as it is. In r5 this means the T4c ledger grant fenced by M1 identities. `prepare_conflict_bootstrap` only
  receives a grant mapping, so no code conflict is expected. T3b's fingerprint (id, after, repo, criteria,
  verification) is unchanged.
- The finding text of T8.1 F1 still says "M1 recovery grant operation" because it is audit history. The appended
  boundary paragraph supersedes it for the fix location.
- Rebasing r4→r5 with ordinary `rebase_run` resets T4, T4a and other changed tasks with a fresh budget. That is the
  owner's normal revision semantics, but r5 changes the content of T4 (8 attempts used).
- Global quiescence briefly holds back new dispatch, and in T4c the owner is stopped twice per application (barrier
  request, then apply). No attempt is cancelled, but there is a visible delay. The barrier and one re-request are
  bounded by `max_recovery_wait`, and a second expiry becomes a durable blocker.
- Storing the ledger in its own SQLite file (instead of the M5 diagnostic store) is a planner decision. It keeps M5
  advisory. A reviewer may prefer to reuse the store.
- History for estimates is unknown for every metric, so the estimates are provisional allowances.
