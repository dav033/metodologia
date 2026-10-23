# PLAN.json schema 1.3.0 — functional subplans (engine v2, F1)

Design record for D-01 / D-02 (Option A: new schema version). Lead: session `59ae629e`, 2026-10-23.
Authority: `CONTRACT.md` §2–3 and master §7. This is the contract every F4 consumer builds on.

## 0. Principles

1. **Additive and optional.** Every 1.3.0 field is optional at the plan level: a 1.3.0 plan without `subplans`
   validates exactly like a 1.2.0 plan with a new version string. 1.0.0–1.2.0 documents validate, canonicalise and
   hash **byte-for-byte as before**.
2. **No 1.3.0 field below 1.3.0.** `subplans`, `composition_gates`, task `subplan_id`, task `ui`, task kind `design`
   and verification `environment`/`requires`/`authorization_needed` in a document whose `schema_version` < 1.3.0
   are `SCHEMA_FIELD_UNSUPPORTED`: an **error at publication** (`check`, approval, `freeze` of a new revision) and a
   **warning** for consumer validation/`load()`, so an already frozen document can never stop loading. (None of the
   5 live plans nor their revisions use these names; a test asserts it.)
3. **One artifact.** Subplans live inside `PLAN.json`; freeze, revision, sha256, `bind_approved` and drift detection
   cover them with no second manifest (atomic by construction).
4. **Single source of truth for membership.** A task names its subplan (`subplan_id`); a subplan never lists tasks.
5. **The planner still never schedules.** No status, version state, ref, model, agent or worker field. Runtime
   identities (`refs/subplans/...`, composition manifests) belong to F4, not to the plan.
6. **Default for new skeletons stays 1.2.0 until F4** enables M1/M2/M6 consumers for 1.3.0
   (`bt_scheduler_core/plan.py` `PLAN_SCHEMA_CAPABILITIES` keeps refusing 1.3.0 until then: fail closed).
   `LATEST_SCHEMA_VERSION = "1.3.0"` is what the validator accepts; `SCHEMA_VERSION` (init default) moves in F4.
   Until then the adapter (`bt_plan_adapter`, which may see consumer capabilities; `bt_planner` may not) refuses
   approval/freeze/handoff/launch of a plan whose version no consumer supports (`PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE`),
   and `compat` reports `consumer_supported`. Refusal happens before the owner approves, not at run time.
7. **Implementation hazard (must):** new task keys go to a separate `TASK_KEYS_13` used only when `schema_13`; the
   1.0/1.1/1.2 key lists, `REQUIRED_TASK_KEYS`, `compat` and every `canonicalize` branch below 1.3.0 stay untouched.
   A test re-hashes every frozen revision under `bitacora/*/requirements/*/plan-revisions/` and every live PLAN.json
   and compares validation output with the `pre-engine-v2` tag's `bt_planner`.

## 1. New top-level fields

### `subplans` (optional list, max 64)

```json
{
  "id": "SP-1",
  "milestone_id": "M1",
  "title": "Customer registration",
  "outcome": "A visitor registers and then finds the customer in the list",
  "covers": ["R1", "R2"],
  "acceptance_criteria": ["A registered customer appears in the list with the submitted name"],
  "produces": [
    {"contract": "customer-api", "version": 1, "defined_by": "T1", "interfaces": ["IF-1"]}
  ],
  "consumes": [
    {"contract": "auth-session", "version": 1, "from": "SP-2", "dependency": "contract"}
  ],
  "checkpoints": [
    {"task": "T4", "purpose": "API contract verified against the real handler before the UI starts"}
  ],
  "integration_test_task": "T7",
  "audit_task": "T8",
  "ui": {"contract": "customer-form", "version": 1, "design_task": "T2", "visual_review_task": "T9"}
}
```

| Field | Rule |
|---|---|
| `id` | `SP-[1-9][0-9]*`, unique |
| `milestone_id` | an existing milestone; **every task with this `subplan_id` has the same `milestone_id`** (D-02) |
| `title` | non-empty text |
| `outcome` | observable result, ≥ 4 words, not equal to `title` (`SUBPLAN_NO_OUTCOME`) |
| `covers` | non-empty, subset of top-level `requirements` |
| `acceptance_criteria` | non-empty; **each criterion is the exact text of an acceptance criterion of one of the subplan's own tasks** (so a check carries it: criterion → evidence) |
| `produces[]` | `contract` slug `[a-z0-9][a-z0-9-]{0,63}`, `version` int 1..1000, `defined_by` = a task of this subplan (or a task with no subplan) that freezes the contract; optional `interfaces` = existing `IF-n` ids. `(contract, version)` produced by at most one subplan |
| `consumes[]` | `contract`+`version` (the contract **major** the consumer is written against; compatible changes do not bump it, F4 decides impact); `from` = another `SP-n` that produces exactly that `(contract, version)`, or `"external"` (outside this plan; then `dependency` must be `contract`); `dependency` ∈ `contract`, `implementation`, `publication`; optional `verified_by` = consumer-side contract test task ids of this subplan (warning `CONSUMER_CONTRACT_TEST_MISSING` when absent for `implementation`/`publication`) |
| `checkpoints[]` | `task` = a task of this subplan whose `kind` is `test` or `audit`; `purpose` non-empty |
| `integration_test_task` | required: a `kind: test` task of this subplan with a `command` verification of category `integration` (real entry points) |
| `audit_task` | required: a `kind: audit` task of this subplan (existing ledger rule applies); it must have **every other task of the subplan** as an ancestor, and `integration_test_task` among them |
| `ui` | optional; see §3 |

Ordering rules derived from `consumes` (all errors, `SUBPLAN_ORDER`). *Exempt consumer tasks* are its
`research`/`docs` tasks and the consumer's own `produces[].defined_by` tasks (so two subplans can freeze contracts
for each other first):

- `dependency: contract` — every non-exempt task of the consumer has the producer's `defined_by` task as an ancestor
  (it builds against a frozen contract, not code).
- `dependency: implementation` — every non-exempt task of the consumer has the producer's `audit_task` as an
  ancestor (never build on unaudited code).
- `dependency: publication` — every non-exempt task of the consumer has, as an ancestor, the `task` of a composition
  gate whose `subplans` include the producer and **exclude the consumer** (the producer's version was published in an
  accepted composition first). The consumer's own integration with the producer is a later gate that lists both.

Cross-subplan edges (`SUBPLAN_EDGE`, error): a task's `after` may name a task of another subplan only if that task is
the other subplan's `defined_by`/`audit_task`, or a gate task, **and** a matching `consumes` edge from this task's
subplan to that subplan exists. Undeclared reliance on another subplan's work is how P-177 happened.

Coupled units: two subplans that need each other's unfinished implementation are one subplan (master §7.2 "unidad
acoplada"); the validator rejects the mutual `implementation`/`publication` cycle instead of offering an escape.

Graph rules:

- Cycles among `implementation`/`publication` edges are errors (`SUBPLAN_CYCLE`). A cycle made only of `contract`
  edges is a warning (mutually consumed frozen contracts are legitimate; mutually consumed unfinished code is not).
- A subplan with no task is an error (`SUBPLAN_EMPTY`).

### `composition_gates` (optional list, max 32)

```json
{"id": "CG-1", "subplans": ["SP-1", "SP-2"], "task": "T12", "audit_task": "T13",
 "criteria": ["Registration uses the real session issued by login"]}
```

| Field | Rule |
|---|---|
| `id` | `CG-[1-9][0-9]*`, unique |
| `subplans` | ≥ 1 distinct existing subplans (one subplan = publishing that subplan's accepted version on top of the previous composition) |
| `task` | `kind: test`, no `subplan_id`, a `command` verification of category `integration`; has every listed subplan's `audit_task` as an ancestor (only accepted versions are composed) |
| `audit_task` | optional `kind: audit` with no `subplan_id`, `task` among its ancestors |
| `criteria` | non-empty; each is the exact text of an acceptance criterion of `task` |

Coverage rule (`COMPOSITION_MISSING`, error): for every `consumes` edge between two subplans of this plan, at least one
gate lists both. Mocks inside a subplan are allowed; integrated acceptance needs the real producer and consumer.

## 2. New task fields (1.3.0)

- `subplan_id` (optional): an existing `SP-n`. A task belongs to at most one subplan (it is a single string).
- `ui` (optional boolean, default absent = false): the task implements user-facing UI. Rules in §3.
- `kind` gains `design`: Designer authors/versions the UI/UX contract. Only valid in 1.3.0.
- Traceability: a task with `subplan_id` has `covers ⊆ subplan.covers`; every requirement of `subplan.covers` is
  covered by at least one task of that subplan.

When `subplans` is non-empty:

- `REQUIREMENT_ORPHAN` (error) when the next rule fails:
- every requirement is in some subplan's `covers` **or** covered by a composition gate `task` (a gate is the
  integration owner of a cross-cutting requirement);
- tasks without `subplan_id` are allowed only for `test` (gates), `audit`, `docs`, `research`; a `kind: implement`
  or `design` task without a subplan is an error (`TASK_OUTSIDE_SUBPLAN`).

## 3. UI and the Designer gate (master §7.5, CONTRACT §3)

`subplan.ui` = `{contract, version, design_task, visual_review_task}`:

- `contract` slug + `version` int: the Designer contract the implementers consume (`design/contracts/<contract>@v<version>.md` in the project repo; the path is a convention, not validated here).
- `design_task`: a `kind: design` task of this subplan.
- `visual_review_task`: a `kind: audit` task of this subplan (Reviewer visual axis; existing ledger rule applies).
- The preview is a **per-project setting** (`design.preview` in the project config, F2), not a plan field. The
  contract is never optional.

Rules (errors unless stated):

- `UI_GATE_MISSING`: a task with `ui: true` whose subplan has no `ui` block, or a `ui: true` task with no
  `subplan_id`.
- `UI_GATE_ORDER`: every `ui: true` task has the subplan's `design_task` as an ancestor.
- `UI_REVIEW_ORDER`: the `visual_review_task` has every `ui: true` task of the subplan as an ancestor, and the
  subplan's `audit_task` has the `visual_review_task` as an ancestor (visual QA before UI acceptance).
- `UI_WORK_UNDECLARED` (**error** in every 1.3.0 plan, with or without subplans): a task without an explicit `ui`
  key whose `expected_paths` end in a UI extension (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.astro`, `.css`, `.scss`,
  `.sass`, `.less`, `.html`). `ui: false` is the explicit acknowledgement (e.g. a `.tsx` route handler). Folder
  names are not used (false positives).

## 4. Verification additions (1.3.0, master §7.7)

Each verification may carry:

- `environment` ∈ `sandbox` (default when absent), `external_authorized`, `production`, `human_attestation`.
- `requires`: list of resource **names** only (`[A-Z][A-Z0-9_]{1,63}` for env vars, or `service:<slug>`); a value
  containing `=`, whitespace or a URL with credentials is an error (`SECRET_VALUE_IN_PLAN`).
- `authorization_needed`: non-empty text, required when `environment` is `production`: what the **owner** must grant
  (the Planner never grants it); scanned for secret values like `requires`.

Rules:

- `EXTERNAL_ONLY_IMPLEMENT` (error): a `kind: implement` task whose every command verification has a non-`sandbox`
  environment (an implementation criterion must be provable in the ordinary sandbox; external smokes belong to
  `test` tasks with a recoverable blocked outcome).
- `human_attestation` requires `type: manual` with `expected`.

## 5. Behavioural checks are not file-existence checks (1.3.0)

`FILE_EXISTENCE_CHECK` (error in 1.3.0, warning in 1.2.0 is **not** added — 1.2.0 output must not change): a command
verification of category `functional`, `integration` or `product` whose command is only a file-existence or
well-formedness probe (`test -s|-f|-e|-d …`, `[ -f … ]`, `ls`, `stat`, `python -m json.tool`, `jq empty`, `cat`,
`head`, `tail`, `wc`, `grep -q`, `diff -q`, `cmp`, `file`, optionally chained with `&&`/`;`) does not prove behaviour.

## 6. Early detection (P-177, master §7.6)

`LATE_CHECKPOINT` (error in every 1.3.0 plan, with or without subplans): the longest dependency chain of
non-barrier tasks (`implement|docs|design|research`) with no barrier (`test` or `audit` task) between its links is
longer than **6**. Inside a subplan only that subplan's own barriers count (`SUBPLAN_LATE_CHECKPOINT`). A subplan with
more than 8 tasks needs at least one `checkpoints` entry. Cross-subplan work can never be built on unaudited code
(`implementation` ordering and `SUBPLAN_EDGE` above).

The P-177 regression fixture is a 24-task plan: in its legacy 1.2.0 shape (one audit at the end) the defects F1–F5
are first observable only by the final audit (24 dependent tasks exposed); in its 1.3.0 shape each of F1–F5 is
mapped to the subplan checkpoint/audit that observes it and the number of tasks downstream of the defect before that
barrier is ≤ 6. The fixture includes a machine-readable map `defect → introducing task → first barrier` and the test
computes the exposure from the plan graph (not from a hard-coded number).

## 7. Canonical form and hashes

- 1.0.0–1.2.0: unchanged (`canonicalize` output identical byte-for-byte; frozen revisions keep their sha256).
- 1.3.0: like 1.2.0 plus `subplan_id`, `ui` in `TASK_KEYS` order after `kind`; `subplans` and `composition_gates`
  are top-level keys sorted with the rest (deep-sorted objects, list order preserved).

## 8. Reports and PLAN.md

- `report` (1.3.0) adds `subplans`: per subplan id, milestone, covers, task ids, produces/consumes, checkpoints,
  audit/integration tasks, ui block, and `exposure` (max tasks downstream of any task before a barrier). Planned, not
  passed.
- PLAN.md task lines gain `subplan: SP-1` and `ui: yes`; compared with PLAN.json like `kind:`. Subplan headings are
  not required (a subplan is not a milestone).
- `plan-status` and the generated status block group tasks by subplan inside each milestone when the plan has
  subplans.

## 9. Stable error codes added

`SCHEMA_FIELD_UNSUPPORTED`, `SUBPLAN_INVALID`, `SUBPLAN_EMPTY`, `SUBPLAN_NO_OUTCOME`, `SUBPLAN_MILESTONE`,
`SUBPLAN_COVERAGE`, `SUBPLAN_CRITERION_UNCARRIED`, `SUBPLAN_CONTRACT`, `SUBPLAN_ORDER`, `SUBPLAN_CYCLE`,
`SUBPLAN_AUDIT`, `SUBPLAN_EDGE`, `SUBPLAN_LATE_CHECKPOINT`, `LATE_CHECKPOINT`, `TASK_OUTSIDE_SUBPLAN`,
`CONSUMER_CONTRACT_TEST_MISSING` (warning), `UI_WORK_UNDECLARED`, `PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE` (adapter),
`COMPOSITION_INVALID`, `COMPOSITION_MISSING`, `REQUIREMENT_ORPHAN`,
`UI_GATE_MISSING`, `UI_GATE_ORDER`, `UI_REVIEW_ORDER`, `SECRET_VALUE_IN_PLAN`, `EXTERNAL_ONLY_IMPLEMENT`,
`FILE_EXISTENCE_CHECK`. Each error line starts with `<CODE>: <where>: …` so consumers can match the code.

## 10. Review log

- 2026-10-23 antagonist design pass: A1 (publication cycle) blocker, A2–A5 major, A6–A8 minor. All accepted and
  folded in above: publication via a gate that excludes the consumer and gates of ≥1 subplan; exemptions for
  `defined_by`/research/docs; `SUBPLAN_EDGE`; implement/design outside subplans is an error; plan-wide
  `LATE_CHECKPOINT` in 1.3.0; `TASK_KEYS_13` + frozen-revision hash test; `UI_WORK_UNDECLARED` by extension as an
  error; engine-capability refusal at approval in the adapter; `preview` moved to project config;
  `authorization_needed`; `verified_by`; gate-owned cross-cutting requirements; wider probe list.
