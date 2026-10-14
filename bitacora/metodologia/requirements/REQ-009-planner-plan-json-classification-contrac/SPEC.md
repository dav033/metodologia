---
id: REQ-009
status: ready
created: 2026-10-14
track: standard
---
# REQ-009 — Planner PLAN.json classification contract

## Problem & goal
Plans are human-readable but their operational metadata (complexity, risk, duration, coupling, shared resources) is
not uniform, so a deterministic Scheduler cannot consume them without re-reading free Markdown.
**Success looks like:** every executable task carries a validated classification in a versioned `PLAN.json`
(schema 1.0.0), kept consistent with `PLAN.md`, frozen per approved revision, validated deterministically.

## Authoritative source
The full requirement, taxonomy (§4), task fields (§5), process (§7), tasks T1-T11 (§8), acceptance AC-01..AC-15 (§9)
and DoD (§14) are in `/home/david/dev/metodologia/PLAN-SUPERIA-FASE-1-PLANES.md` (owner-provided, 2026-10-14).
This SPEC does not restate them; where they conflict with this file, that document wins.

## Out of scope
Scheduler/Monitor/Recovery engine, model/account/worker selection, concurrency decisions, rewriting any `RUN.json`,
new services or databases, retroactively classifying historical plans.

## Constraints
- Stdlib-only Python (`pyproject` `dependencies = []`); no `jsonschema` dependency, so the validator is hand-written
  and the JSON Schema file is published as the contract document.
- File guard: new logic goes in new `bt_*.py` modules (`bt_runstate.py` and `bt_run.py` sit at 500 lines).
- Existing `PLAN.md` task-line grammar (`bt_runstate.parse_plan`) must keep working unchanged.
- No commit/push authorized; preserve unrelated uncommitted work in the repo.

## Assumptions (rulings on §15 open decisions)
1. Schema at `skill/schemas/plan.schema.json`; Python validator `bt_plan_contract.py` (tests with unittest).
2. `PLAN.json` owns the classification; `init` derives a skeleton (ids, milestones, after, verify, files, repo) from
   `PLAN.md`; `check` cross-checks ids/milestones/dependencies between both. No classification is ever defaulted.
3. Approval freezes a revision into `plan-revisions/PLAN.r<N>.json` (+sha256); edits to a frozen revision are an error.
4. Legacy plans without `PLAN.json` stay valid for the old flow; `compat` reports what is missing, read-only.
5. Undeterminable duration blocks publication: the planner must add a research task or decompose (no formal exception
   path, to avoid precise-looking numbers). `confidence=low` is allowed only with a number and a rationale.
