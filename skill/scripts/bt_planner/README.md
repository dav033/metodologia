# bt_planner — the planner module

Part of the methodology, isolated by construction. It **describes and classifies work**: a human `PLAN.md` next to a
validated, versioned `PLAN.json` that a deterministic scheduler can read without interpreting prose. It inspects nothing
about who will run the work: it never picks a model, account or worker count, never supervises, and never writes
execution state. Only three things are written: `PLAN.json` (`init`), `plan-revisions/` (`freeze`) and the append-only
`PLAN.amendments.jsonl` (`amend`: how hard a task turned out to be, never what to build).

## Boundaries (enforced by `tests/test_boundaries.py`)

- Imports only the Python standard library and itself. No other `bt_*` module, no third-party package.
- Names no methodology path or file (`bitacora`, `RUN.json`, `~`): it works on **a directory you pass in**.
- Everything it needs travels inside the package: parser, lock, schema (`data/plan.schema.json`), example
  (`data/plan.example.json`), CLI, tests.
- The rest of the methodology reaches it through one adapter, `skill/scripts/bt_plan_adapter.py`. The dependency points
  one way only: adapter → `bt_planner`.

## Layout

| File | Role |
|---|---|
| `contract.py` | enums, validator, canonical JSON, `load`, `PlanContractError`, `Report` |
| `amendments.py` | classification amendments during a run (`PLAN.amendments.jsonl`): `append`, `read`, `effective`, `direction` |
| `revisions.py` | immutable approved revisions (`plan-revisions/`), manifest + sha256, `run_reference` |
| `markdown.py` | the `PLAN.md` task-line / milestone grammar (own parser) and what it would otherwise drop silently |
| `evidence.py` | classification evidence (schema 1.1.0): typed references, justification quality, confidence rules |
| `traceability.py` | SPEC requirement extraction and requirement-to-task coverage validation/projection |
| `interfaces.py` | cross-task interface validation and report projection |
| `quality.py` | plan coherence, verification findings and the `report` summary |
| `sync.py` | skeleton from PLAN.md, PLAN.md ↔ PLAN.json consistency, `check`, approval freeze, the launch gate `bind_approved`, compat report |
| `_lock.py` | exclusive lock for one plan directory |
| `cli.py`, `__main__.py` | command line |
| `data/` | bundled JSON Schema and example plan |
| `tests/` | the module's own suite (run from anywhere) |

## Command line

All actions: `python -m bt_planner <action> [directory|file] [--plan-id ID] [--force] [--json] [--approved-states a,b]`
(run with the folder that contains `bt_planner` on `PYTHONPATH`, or from it). Exit code 0 = ok, 2 = invalid or refused.

- `python -m bt_planner init <dir>` derives the skeleton from `<dir>/PLAN.md` and the referenced SPEC's `Requirements`
  section; `covers` starts empty unless PLAN.md declares it, and missing classifications and verification categories
  are reported as gaps (never defaulted). It refuses an ambiguous PLAN.md (`PLAN_MD_AMBIGUOUS`).
- `python -m bt_planner check <dir> [--repo ROLE=PATH ...]` is the publication gate: schema, unique ids, existing
  references, no cycles, no dependency on a later milestone, no orphan milestone, classification evidence, unordered
  tasks that share a path or resource, PLAN.md ↔ PLAN.json agreement (below) and frozen-revision integrity. With `--repo`
  the `file:` evidence is verified against the checkout; without it the report says it was not verified.
- `python -m bt_planner freeze <dir>` freezes the checked PLAN.json as the next revision (the approval act).
  `PLAN.md` front matter `status:` must be one of `approved, launched, done, merged` (override with
  `--approved-states`).
- `python -m bt_planner bind <dir>` is the launch gate, read-only: PLAN.json is valid and **is exactly** the latest
  frozen (approved) revision. `python -m bt_planner report <dir>` prints the quality summary (critical path in minutes,
  widest level, distributions, tasks without a machine-checked verification, evidence coverage and collisions). Schema
  1.2.0 adds `coverage`, declared `interfaces`, `verification_categories` and `criteria_without_command`; 1.0.0/1.1.0
  report shapes stay unchanged.
- `python -m bt_planner show <dir>` lists frozen revisions.
- `python -m bt_planner compat <dir>` is read-only: what an existing plan already provides and what needs explicit
  enrichment (legacy `complexity:`/`risk:` values are reported verbatim as legacy labels, never converted).
- `python -m bt_planner validate <file>` validates one PLAN.json on its own, e.g. a scheduler's input.
- `python -m bt_planner schema` / `python -m bt_planner example` print the bundled schema / example.

`plan_id` defaults to the `REQ-042` style prefix of the directory name (`REQ-042-some-slug`), otherwise the directory name.

## Python API

```python
import bt_planner as planner
plan = planner.load(path_to_plan_json)                 # validated, read-only; raises PlanContractError
report = planner.check(directory)                      # Report(errors, warnings, ok)
entry = planner.approve_freeze(directory)              # {revision, sha256, frozen_at}
frozen = planner.load_revision(directory, 1)           # what an executor ran, hash-verified
fields = planner.run_reference(directory)              # {"plan_ref": {...}} | {"plan_ref_error": code} | {}
```

```python
entry = planner.bind_approved(directory, plan_id, states, repo_roots=roots)   # the gate every launch passes
```

Files that exist before the module is used: `PLAN.md` (the narrative; grammar below), `SPEC.md` (target of `spec_ref`).

## PLAN.md grammar understood

```
### M1 — Milestone title
- [ ] T1 — Task title · repo: backend · after: T0, T0a · verify: `pytest -q` · files: src/a.py · resources: db · covers: R1, R2 · kind: test
```

Task ids `T1`, `T2.1`, `T3a`; milestone headings `###`/`####` with `M<number>`; fields separated by ` · `; `verify` only
when backticked; unsafe `files` (absolute or `..`) are dropped; HTML comments ignored. Planner sync checks `covers`
and `kind` for schema 1.2.0; `covers` remains Planner metadata and is not added to the supervisor's runtime parser.
Parser parity continues comparing their shared fields on real plans.

### PLAN.md ↔ PLAN.json agreement

`check` compares everything a task line states structurally, never free prose. Contradictions are errors:

| PLAN.md | against PLAN.json |
|---|---|
| a task id (or milestone heading with another title) defined twice | rejected on its own, before any comparison |
| `T1 — title` | `title` (spacing, case and `*`/backticks ignored) |
| `repo: x` | `repository` |
| `after: …` | `after`, as a set; an entry that is not a task id, or a repeated one, is an error |
| `verify: \`cmd\`` | one `command` verification with exactly that value (extra ones are fine; a `verify:` that is not backticked is an error) |
| `files: a, b` / `resources: x` | every stated entry must be in `expected_paths` / `shared_resources` (JSON may add more, never drop) |
| `risk: low / medium / high` | `risk` (other legacy words are never converted) |
| `covers: R1, R2` (schema 1.2.0) | task `covers` IDs, as a set |
| `kind: implement` (schema 1.2.0) | model-agnostic task `kind` |
| `### M1 — title` | milestone `title`; the set of milestones and each task's membership |

What PLAN.md does not state is not a contradiction. A field repeated on one line, an unusable `files:`/`resources:`,
a misspelt field (`repository:` for `repo:`) and a checkbox line with a near-miss id (`t1`, `T-5`) are reported with
their line instead of being dropped. Duplicate ids in PLAN.json name their `tasks[i]` positions.

## The contract (schema 1.2.0)

Per task, all required (no `null`, no silent defaults): `id`, `milestone_id`, `title`, `objective`, `repository`,
`after` (`[]` if none), `acceptance_criteria` (observable, non-empty), `verification` (`{type: command|manual, value,
purpose}`; `manual` also needs `expected`; optional `created_by: T<n>` for a test the plan itself creates),
`complexity`, `scope`, `estimated_minutes`, `risk`, `coupling`, `confidence`, `estimate_rationale`,
`classification_evidence` (required from 1.1.0, below), `expected_paths`
(guidance, may be `[]`), `shared_resources` (`[]` if none known). From 1.2.0 every task also requires non-empty `covers`
(IDs declared at the top level) and `kind` (`implement`, `test`, `docs`, `audit`, `research`). Each verification also
requires `category` (`static`, `functional`, `integration`, `regression`, `product`), separate from `type`.
Per milestone: `id`, `title`, `acceptance_criteria`.
Top level: `schema_version`, `plan_id`, `revision` (1..1000000), `spec_ref` (relative path inside the directory),
`milestones`, `tasks`, and from 1.2.0 non-empty unique `requirements` IDs matching the SPEC Requirements section.
Optional `interfaces` declare producer/consumer contracts and integration criteria. Extra fields are allowed, except scheduling/execution keys (`model`, `agent`, `account`,
`workers`, `status`, `attempts`, `sessions`, `cost`…, and any key made of a scheduling word such as `model_hint`,
`assignee`, `executor`, `llm`, `max_parallel`, `numWorkers`) which are rejected at any nesting level. Ids use ASCII digits;
NaN/Infinity are rejected; `estimated_minutes` is 1..100000 (a warning above 480: consider splitting).

The `report` fields describe planned coverage, declared interfaces and verification evidence only. They do not mean that
requirements are accepted or integration has run. Until the coordinated T11 M1/M2/M6 compatibility migration and its
fail-closed capability check are complete, do not approve, hand off, launch or resume a schema 1.2.0 plan.

`coverage` maps each requirement ID to its planned task IDs (an empty list is uncovered); `interfaces` lists the
declared producer/consumer contract; `verification_categories` groups declared checks by requirement; and
`criteria_without_command` lists criteria whose verification does not provide one unique exact-purpose command for M6.
None of these projections is an acceptance boolean.

## Schema 1.3.0

1.3.0 adds optional `subplans` and `composition_gates` in PLAN.json, plus task `subplan_id`/`ui`, the `design` task
kind, and verification `environment`, `requires` and `authorization_needed`. A subplan owns task membership and
requirement coverage, freezes its contracts, names an integration test and a final audit, and can declare checkpoints
and a UI design/visual review contract. Composition gates record integration across accepted subplans. The Planner
validates dependency order, declared cross-subplan edges, requirement coverage, UI review order, resource names,
behavioral verification and early checkpoints; it never assigns execution or grants authorization.

Every diagnostic added for 1.3.0 starts with its stable code (`SUBPLAN_*`, `COMPOSITION_*`, `UI_*`,
`REQUIREMENT_ORPHAN`, `LATE_CHECKPOINT`, `SECRET_VALUE_IN_PLAN`, `EXTERNAL_ONLY_IMPLEMENT`,
`FILE_EXISTENCE_CHECK`, `UI_WORK_UNDECLARED`, `SCHEMA_FIELD_UNSUPPORTED`,
`CONSUMER_CONTRACT_TEST_MISSING`). A 1.3.0-only field in an older plan warns during consumer validation and errors at
publication. Canonical ordering and hashing add the new fields only for 1.3.0; 1.0.0–1.2.0 serialization stays fixed.
`LATEST_SCHEMA_VERSION` is 1.3.0, while new skeletons remain 1.2.0 until engine consumers support the version.

### Rubric (the dimensions are independent)

- **complexity** = reasoning needed, not time, file count or model quality. `low` known localized solution · `medium`
  some investigation/decisions · `high` cross-component reasoning or relevant uncertainty · `extreme` exceptional
  uncertainty or far-reaching architectural decisions.
- **scope** = size of the change: `isolated_fix` · `small_change` · `large_change` (extensive/transversal) ·
  `full_feature` (verifiable end to end) · `full_system` (**decompose it**; only with `scope_exception: {reason}`).
- **estimated_minutes** = integer for one reasonable run including local verification; an estimate, not a limit. If no
  number can be defended, do not publish: split the task or add a research task first.
- **risk** = impact of a mistake: `low` local, reversible, caught by simple tests · `medium` possible functional
  regression or shared contract · `high` security, data, permissions, compatibility, production, payments or hard to revert.
- **coupling** = interaction with other tasks: `low` independent · `medium` shared contracts/resources need coordination ·
  `high` tight interaction or high conflict potential. A signal for a scheduler, never permission to parallelise.
- **confidence** (of the estimate): `high` code investigated, precedent or direct evidence · `medium` partial evidence ·
  `low` preliminary or depends on relevant unknowns. `low` is allowed; say why in `estimate_rationale`.

| Case | complexity | scope | risk | coupling | Note |
|---|---|---|---|---|---|
| Two-line fix of an authorization check | low | isolated_fix | high | medium | easy but sensitive; shares the session contract |
| Mechanical rename across 80 files with codemod | low | large_change | medium | high | big, not hard; many tasks touch the same paths |
| Change a public API response shape used by two clients | high | large_change | high | high | cross contracts; name the contract in `shared_resources` |
| New report page with its own endpoint and tests | medium | full_feature | medium | low | end-to-end, self-contained |
| Replace the persistence layer | extreme | full_system | high | high | **decompose** (adapter, migration, cutover…) or file an exception |
| Add a CSS token to one component | low | small_change | low | low | trivial everywhere |
| Investigate why a job is flaky, outcome unknown | medium | small_change | low | low | `confidence: low`; likely precedes a fix task |

Honesty rules: planned tests that do not exist yet are work items (`created_by`), never evidence; manual checks state the
expected result; do not attribute success that was not executed; distinguish "classification not available" from "estimated".

### Classification evidence (schema 1.1.0)

A bare label is not a classification. From `1.1.0` each task carries `classification_evidence`, one
`{justification, evidence[]}` per dimension: `complexity`, `scope`, `duration`, `risk`, `coupling`, `confidence`.

```json
"risk": {"justification": "a wrong check locks valid users out or lets expired sessions in; it is auth code",
         "evidence": ["file:src/auth/session.py", "spec:SPEC.md#security"]}
```

References are `kind:value`: `file:` (a concrete path the planner inspected, never `*`/`.`; verified against the
checkout), `command:` (`<cmd> -> <what it showed>`; the arrow and a result are required), `precedent:` (a
requirement/task id like `REQ-009/T4`, a decision or pending id, a commit hash or a URL), `spec:` (a file of the
requirement folder that must exist; an anchor `#x` must match one of its headings, and without an anchor it is context,
not support), `task:` (another task of this plan, never itself), `assumption:` (explicit and unverified: allowed,
never support). `file:` evidence that cannot be verified (no checkout on this machine) is a warning for a plain `check`
and an **error at approval and launch**. Where the methodology can look (through the adapter) a `command:` must name an
executable or path that exists and a `precedent:` a requirement/task, decision, pending item or commit that exists; a
reference that is verifiably absent is always an error. Enforced as errors for `1.1.0`, warnings for `1.0.0` documents (which keep loading;
`check` refuses to publish a *new* revision below `1.1.0`):

- every dimension has a justification of at least 4 words that is not a placeholder, and its own text (no sentence
  pasted under several dimensions);
- `confidence: high` cannot rest on assumptions for complexity/scope/duration and needs evidence that something was
  inspected or run (`file`/`command`/`precedent`);
- `coupling` medium/high names a shared resource or the task it interacts with;
- objective states a result (not the title), acceptance criteria are observable (≥ 3 words, no duplicates), a
  verification command must be able to fail (`true`, `echo ok` are rejected);
- two tasks that nothing orders (`after`, transitively) and that share an `expected_paths` pattern or a
  `shared_resources` entry cannot claim `coupling: low` (order them or raise the coupling);
- free text (objective, rationale, justifications, criteria) that promises parallel safety (`safe to run in parallel`,
  `se puede ejecutar en paralelo`, `paralelizable`…) is refused: `coupling` is a signal, the scheduler decides;
- warnings: `risk: high` verified only manually, a justification reused by three tasks, a justification that shares no
  term with its task or evidence, redundant `after` entries.

The textual rules cannot judge truth; they remove the cheap ways of asserting without arguing, and `file:`/`spec:`/
`task:` references are checked against what exists.

## The launch gate

`bind_approved` is what every path that starts work goes through (standard launch, web approve-and-launch, handoff,
foreground transition and the new-run entry itself): the plan must be valid, consistent with PLAN.md and **exactly the
approved revision**. The approved revision is the latest frozen one; the approval act (`plan approve`, web approval, or
`freeze`) is what freezes it. At launch:

- no PLAN.json and nothing ever frozen → legacy plan, nothing to bind;
- PLAN.json removed after a freeze → `PLAN_MISSING`;
- not approved (and not an explicit `--force`) → `PLAN_NOT_APPROVED`; invalid or contradicting PLAN.md → `PLAN_INVALID`;
- equal to the latest frozen revision → bound, nothing written; the PLAN.md prose is compared too (digest recorded in
  the manifest at approval, ignoring front matter, dated log lines and checkbox marks): changed prose is
  `PLAN_PROSE_DRIFT`;
- different (an edit after approval, or a new revision number nobody approved) → `PLAN_DRIFT`; a launch never turns
  an unreviewed edit into a revision;
- a run that is only being RESUMED keeps its RUN.json untouched but, if the plan has frozen revisions or the run
  carries `plan_ref`, PLAN.json must still exist, be valid and be the latest approved revision (`resume_problem`; file evidence is not
  re-verified there, the run's own work may have moved those files);
- nothing ever frozen (approved by editing `status:` by hand) → `PLAN_NOT_FROZEN`: there is no record of what was
  approved and **a launch never creates it**. Approve with `plan approve` (or run `plan-json freeze` once the owner
  accepted exactly that PLAN.json). An explicit `--force` is the owner's own approval and is the only launch that
  freezes (`source: launch-forced`).

The manifest records how each revision was frozen (`source`: `approval` or `launch-forced`; shown by `show`).

## Revisions

Serialisation is canonical (fixed key order, UTF-8, trailing newline). Schema 1.1.0 also sorts nested keys; schema
1.2.0 adds its fields after legacy contract fields. A 1.0.0 document keeps byte for byte the text it was frozen with,
so the hash of a revision frozen before 1.1.0 never moves
(verified against the previous implementation).

`freeze` writes `plan-revisions/PLAN.r<N>.json` (canonical text, read-only, created exclusively) and appends to
`plan-revisions/MANIFEST.json` under a lock. A frozen revision never changes: editing PLAN.json afterwards makes `check`
fail until `revision` is bumped to N+1. An orphan revision file left by an interrupted freeze is adopted when identical
and refused otherwise. `run_reference` gives an executor the three fields it should remember (`plan_id`, `revision`,
`sha256`) instead of copying the plan.

## Error codes

`PlanContractError.code` is stable; `issues` are actionable lines naming the task and field.
Reading: `PLAN_NOT_FOUND`, `PLAN_UNREADABLE`, `PLAN_NOT_JSON` (also NaN/Infinity and absurd nesting), `PLAN_TOO_LARGE`,
`PLAN_NOT_SERIALISABLE`, `PLAN_INVALID` (e.g. `T3.risk: 'critical' is not one of low, medium, high`).
Launch gate: `PLAN_MISSING`, `PLAN_DRIFT`, `PLAN_PROSE_DRIFT`, `PLAN_NOT_FROZEN` (and `PLAN_NOT_APPROVED`, `PLAN_INVALID` above).
Revisions: `REVISION_UNKNOWN`, `REVISION_TAMPERED`, `REVISION_FROZEN`, `REVISION_ORDER`, `REVISION_STORE_DAMAGED`,
`REVISION_STORE_UNREADABLE`, `REVISION_STORE_UNSAFE` (symlinked directory), `REVISION_STORE_UNWRITABLE`,
`REVISION_STORE_BUSY`. CLI-side refusals: `PLAN_EXISTS`, `PLAN_MD_EMPTY`, `PLAN_MD_AMBIGUOUS`, `PLAN_NOT_APPROVED`.

## Verify it

```
cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -v          # the module's own suite
python3 -I -m unittest discover -s bt_planner/tests                             # same, isolated interpreter
```

`tests/test_isolation.py` copies the package alone to a temporary directory and runs this suite and an end-to-end CLI
session there with `python -I`, so nothing from the methodology can be silently relied on.


## Amendments (classification changes while a plan runs)

An approved revision never changes. How hard a task turned out to be (`complexity`, `scope`, `risk`, `coupling`,
`confidence`, `estimated_minutes`) does change once the work reveals it, so the change is recorded in
`PLAN.amendments.jsonl` (one JSON object per line, append-only, written under `.amend.lock`):

```json
{"seq": 1, "task": "T4", "field": "complexity", "from": "medium", "to": "high", "reason": "...", "evidence": ["file:..."],
 "by": "claude", "proposed_by": "agent", "at": "2026-10-18T22:00:00+00:00", "plan_ref": {"plan_id": "REQ-026", "revision": 1}}
```

`python -m bt_planner amend <dir> --task T4 --field complexity --to high --reason "..." --evidence file:x --by claude
--proposed-by agent` appends one; `amendments <dir>` lists them. Rules: only classification fields with valid values;
`from` must equal the value in force (a stale one is refused on append and ignored on read); raising a level may be proposed
by an agent **with evidence**, lowering needs `--proposed-by owner`; amendments bind to the revision they were written
against and do not carry to revision N+1 (a new revision restates the classification). `amendments.effective(plan, read(dir))`
is the classification in force; consumers use it for the NEXT decision, never to rewrite history. Stable error codes:
`AMEND_FIELD`, `AMEND_VALUE`, `AMEND_NOOP`, `AMEND_REASON`, `AMEND_AUTHOR`, `AMEND_TASK`, `AMEND_EVIDENCE`,
`AMEND_LOWER_NEEDS_OWNER`, `AMEND_NO_PLAN`, `AMEND_UNREADABLE`, `AMEND_FULL`.
