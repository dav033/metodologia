# Planner module: classified plans and `PLAN.json`

Read this when you write, validate, freeze or consume a plan that will run through the scheduler. The logic
lives in the **module `skill/scripts/bt_planner/`** (see its `README.md` for the contract, the classification rubric with
boundary examples, the PLAN.md grammar, revisions and the stable error codes). This page only says how the methodology
uses it. Design source: `PLAN-SUPERIA-FASE-1-PLANES.md` (REQ-009); isolation: REQ-010; convention: `modules.md`.

The planner **describes and classifies** work. It never chooses the model, account or worker count, never supervises,
never writes run state: it inspects, writes, validates, hands over and ends.

## Files

| File | Owner | Role |
|---|---|---|
| `SPEC.md`, `PLAN.md` | planner | what/why and the human narrative (schema 1.2.0 adds `covers:` and `kind:` annotations) |
| `PLAN.json` | planner | the classified, validated contract the scheduler reads |
| `plan-revisions/PLAN.r<N>.json` + `MANIFEST.json` | planner at approval | immutable approved revisions with sha256 |
| `HANDOFF.md` | launch | context for a fresh executor session |
| `SCHEDULER.db` + `RUN.projection.json` | scheduler | execution state (the database is the authority; the projection is a read model carrying the `plan_ref`). `RUN.json` is legacy: read-only for old runs and for the foreground/delegate path |

Checkboxes in `PLAN.md` are presentation, and so is the generated status block between `<!-- bitacora:status:begin -->` and
`<!-- bitacora:status:end -->` (progress, difficulty, model and account; ignored by the drift check; PLAN.json never gets
those keys). The scheduler run database is authority on state. A plan without a frozen `PLAN.json` is refused at launch
(`PLAN_NOT_FROZEN`).

## Planner flow

1. Inspect the real project; never copy paths, commands or tests from another plan without checking they exist.
2. Write `SPEC.md` and `PLAN.md` as usual (milestones `### M1 — …`, task lines with `after:` and backticked `verify:`;
   schema 1.2.0 task lines may also state `covers:` and `kind:`).
3. `bitacora.py plan-json init REQ-NNN` derives the skeleton and requirement IDs from `SPEC.md`'s `Requirements`
   section. Each task starts with empty `covers` unless PLAN.md declares coverage; missing fields remain gaps.
4. Fill the classification and requirement coverage in `PLAN.json` (rubric: `bt_planner/README.md`). **Argue every dimension**: schema 1.1.0 needs
   `classification_evidence` per task (justification of at least 4 words + typed references `file:`, `command:`,
   `precedent:`, `spec:`, `task:`, `assumption:`). Cite files you actually opened; `confidence: high` cannot stand on
   assumptions; an unknown stays `confidence: low` with a research task before the work that depends on it.
5. `bitacora.py plan-json check REQ-NNN` (exit 2 on any error) is the publication gate: schema, evidence (`file:`
   references are verified against the project's registered repositories; unverifiable ones are an error at approval and
   launch), PLAN.md ↔ PLAN.json agreement and unordered tasks that collide. For schema 1.2.0 it also validates
   requirement coverage, interface contracts, task `kind` and verification `category`. Fix and rerun; do not present an
   invalid plan for approval. `plan-json report REQ-NNN` adds planned coverage, declared interfaces and verification
   projections for 1.2.0; these are not acceptance verdicts.
6. Approval freezes: `plan approve` (terminal), the web button and `handoff` validate PLAN.json and freeze exactly that
   revision (an invalid plan cannot be approved). **A launch never freezes**: a plan approved by editing `status:` by
   hand is refused with `PLAN_NOT_FROZEN` until `plan-json freeze REQ-NNN` records the approval (there is no `launch --force`). Later scope changes mean `revision: N+1` and a new approval.
   **Enforced, not just asked:** the Stop hook holds a session that wrote or ran planning commands for a draft/review
   requirement (`bt_plan_gate`, up to 3 times per requirement) while its PLAN.json is missing or fails `check`, and the
   plan page shows a red "Plan sin clasificar" banner and `sin clasificar` on each task. A plan with no difficulty is a
   broken contract, never "an easy plan". `bitacora.py go REQ-NNN` classifies it through the Planner and runs it.
7. Close the planning session; a later session reads `PLAN.json` / `plan-revisions/` only. Nothing here launches agents.

`plan-json show REQ-NNN` lists revisions; `plan-json compat REQ-NNN` is read-only and reports what a legacy plan lacks
(and any ambiguity in its PLAN.md). Schema 1.0.0/1.1.0 plans already frozen keep working; new revisions use 1.2.0.
Do not approve, hand off, launch or resume a 1.2.0 plan until the T11 M1/M2/M6 compatibility migration and its
fail-closed capability check are complete.

### What `check` compares between PLAN.md and PLAN.json

Ids defined once on both sides, milestone membership and titles, task titles, `repo:` against `repository`, `after:`
(as a set), a stated `verify:` against a command verification, a legacy `risk: low|medium|high`, and, for schema 1.2.0,
explicit `covers:` and `kind:` values. A value PLAN.md does not
state is not a contradiction; one it states differently is an error. Fields the parser would silently drop (a repeated
field, an `after` entry that is not a task id, an unbackticked `verify`) are reported with their line.

### Tracked generated outputs (optional, all 1.x plans)

Top-level `generated_paths` declares build outputs tracked in git, relative to each repository root:

```json
{
  "generated_paths": ["registry.json", "registry/**/registry.json", "catalog/resolved.ts"],
  "generated_command": {"app": "npm run registry:build"}
}
```

Paths use case-sensitive `fnmatch` globs (`*` also matches `/`); an exact entry matches only that path. The list has
at most 256 entries, each 1..1024 characters. Absolute paths, empty or dot path components (`.`/`..`), backslashes,
colons, control characters and leading/trailing whitespace are rejected. An empty list declares no outputs.
`generated_command` is optional metadata: either a non-empty command string for the plan or a non-empty map of
at most 256 repository roles to commands. Roles match `[A-Za-z0-9._-]{1,128}`; each command is at most 4096 characters
and contains no NUL. Commands are not automatically executed.

On the integration line, conflicts only in declared outputs take the candidate's version (including its deletion),
preserving all other cleanly merged files. Last writer means the last applied contribution in deterministic plan order;
candidate previews apply last to the current tip. Mixed conflicts reject the whole contribution and list only source
paths. `LineState.generated_stale` and `Line.apply(...).generated_stale` expose the sorted/taken output paths; `apply`
still unpacks as `(tip, conflicts)`. The marker is conservatively retained during replay and recomputed from accepted
snapshots after restart. It does not assert that the outputs represent the combined sources. Rebuild execution and
clearing the marker after a verified rebuild remain follow-up work; consumers must inspect the marker before release.
No declaration preserves existing integration behavior. These declarations do not change scheduler resource reservations.

`check` warns when unordered tasks in the same repository list the same likely generated path (`registry.json`,
`*.lock`, `*.snap`, `resolved.*`, or a `generated`/`dist` component) without declaring it. Transitive `after` edges
suppress that warning. Declared outputs are exempt from path coupling advice/errors; source overlaps and shared
resource checks still apply. Declarations and rebuild commands are frozen with the rest of the approved plan.

### Audits and end-to-end tests (schema 1.2.0 errors)

A passing `test -s report.md` says nothing about what an audit found, and module tests that pass alone say nothing
about components started together. So `plan-json check` refuses a plan with a `kind: audit` task that

- does not list **exactly one findings ledger** among its `files:` (a path ending `.findings.json`; format and gate in
  `modules.md` §Audit gate), or
- has no `kind: test` task with a command verification of category `integration` among the tasks it follows. That
  test must start the real entry points (server, worker, CLI) together and drive one real flow; importing the
  modules is not an integration test.

`plan-json retrofit-audit REQ-NNN [--cross-check]` fixes the first rule on a plan written before it existed: it gives each audit task its
ledger path (next to its `.md` report) in PLAN.json (a new working revision) and on its PLAN.md `files:`. With `--cross-check` it also clones a lone audit into an independent second one (the owner's `gates.second_auditor`
policy requires a pair). It never
invents the integration test; `check` keeps saying so until the plan has one.

## Where the methodology touches the module

Only `bt_plan_adapter.py` imports `bt_planner` (enforced by `tests/test_plan_integration.py`):

- `bt_cli_plan.py` → `adapter.run_cli` : the `plan-json` command (requirement folder → plan directory, approved words,
  repository roots of the project so `file:` evidence is verified).
- `bt_handoff.assess` → `adapter.handoff_problems` : an invalid `PLAN.json` is a problem, so `handoff` refuses it.
- `bt_rounds.plan_decide` (approve) → `adapter.publishable_problem` before, `adapter.freeze_approved` after: an invalid
  PLAN.json cannot be approved and the approved bytes are frozen as that revision.
- **The launch gate** `adapter.launch_problem` / `freeze_on_launch` (planner `bind_approved`): valid, consistent with
  PLAN.md and exactly the latest frozen revision. Every path that starts work goes through it:
  `bt_launch.launch` (standard, web approve-and-launch, handoff; a dry run verifies without writing), `bt_orchestration_transition.launch` and its successor helper (foreground),
  and `scheduler-run` for any NEW run. A resumed run is never touched by the gate, and it refuses to go on when PLAN.json is no longer
  the latest approved revision, its prose changed, or the run was started under an older revision than the approved
  one (`resume_problem`: `PLAN_REF_STALE` = start a new run). The gate fails closed: an unexpected error is `PLAN_CHECK_FAILED`.
- The scheduler records `plan_ref {plan_id, revision, sha256}` for NEW runs only; existing legacy `RUN.json` files are never touched.

Outcomes: `PLAN_NOT_APPROVED`, `PLAN_INVALID`, `PLAN_MISSING` (PLAN.json removed after a freeze), `PLAN_NOT_FROZEN`,
`PLAN_DRIFT` (an edit or an unapproved new revision: approve it with `plan approve` or `plan-json freeze`; a launch
never freezes an unreviewed edit) and `PLAN_PROSE_DRIFT` (PLAN.md prose changed after approval; front matter, dated
log lines and checkbox ticks are ignored). A plan approved by hand and never frozen has no approval record and is refused (`PLAN_NOT_FROZEN`). A test
(`LaunchPaths`) fails if a new module creates run state around the gate.

## A plan that evolves while it runs

An approved revision is immutable, but the work reveals things. Two mechanisms, split by what changed:

- **Classification** (complexity, scope, risk, coupling, confidence, estimate): `bitacora.py plan-json amend REQ-NNN T4
  complexity high --reason "…" --evidence file:… [--proposed-by agent]` appends to `PLAN.amendments.jsonl` (planner
  `amendments.py`) with old value, new value, reason, evidence, who and when. No new revision and no reapproval: it changes
  how the task is estimated, not what is built. An agent may only **raise** a level and needs evidence; **lowering** needs
  `--proposed-by owner`. M2 reads the classification in force at its NEXT decision (`DecisionAssignmentPort`'s overlay);
  an attempt already running keeps its route. M1 notes it in the audit (`amendment_applied`, an observation: no state
  changes). Amendments bind to the revision they were written for and do not carry to N+1.
- **Scope** (add, remove or split tasks, change criteria or verification): always a new revision (`plan-json freeze`,
  owner-approved). The run then continues on it with `scheduler-run REQ-NNN --rebase`: M1's `rebase_run` keeps accepted
  tasks whose fingerprint (id, prerequisites, repository, criteria, verification) is unchanged and whose prerequisites were
  kept, returns everything else to `pending` with a fresh attempt budget, adds new tasks and drops removed ones. Refused
  while an owner process holds the run or any attempt is alive. Audited as `run_rebased {from_rev, to_rev, kept, reset,
  added, removed}`. The web shows each amended value as `~~medium~~ → high` with who and when, and a timeline of revisions
  and amendments on the plan page.

## Verify

`cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` (the module alone, isolated copy included) and the
methodology suite `python3 -m unittest discover -s tests` from `skill/scripts`.


## Recovery revisions (REQ-029, REQ-030)
A revision made by recovery or by the scheduler's self-healing (`source` `recovery`, `remediation`, `healing`) is an ordinary frozen
revision: it only adds tasks (`T7.1`, `kind: implement`, built from evidence, verified by the owners' own checks) and prerequisites, or
renames a check's `purpose` to its criterion's exact text; it never lowers a check or drops a criterion. `scheduler-op REQ heal revert CASE`
freezes the next revision without the added task. Rebasing onto it keeps every accepted task whose own content is unchanged
(`gates.rebase_cascade: content`).

## Checks map to criteria by exact text
The verifier compares a check's `purpose` with the acceptance criteria of its task character by character. `plan-json check` warns for a check whose purpose is no criterion (`CHECK_UNMAPPED`, with the closest criterion), a criterion no check carries (`CRITERION_UNVERIFIABLE`) and a criterion proven only manually (`CRITERION_MANUAL`: the run waits for `scheduler-op REQ attest`). `plan-json freeze` (the approval) refuses the first two unless `--force` or `planner.require_mapped_checks=false`; revisions the scheduler makes itself (healing, remediation, recovery) are not gated, and plans already frozen are not re-gated.
