# REQ-012 — Report: Planner phase 1 closed

Date 2026-10-14 · owner's `/goal` · decisions D-021 · traceability `AC-TRACE.md` · trials `planning-trials/`.

## What changed

| Area | Change | Where |
|---|---|---|
| PLAN.md ↔ PLAN.json | PLAN.md ambiguities reported with line (id/heading twice, repeated field, non-id `after`, unusable `files`/`resources`, unbackticked `verify`); `check` compares id uniqueness on both sides, task and milestone titles, `repo`↔`repository`, `after` (set), stated `verify` ↔ command verification, legacy same-scale `risk`; both layers always evaluated; `init` refuses an ambiguous PLAN.md | `bt_planner/markdown.py`, `sync.py` |
| Launch gate | `bind_approved`: valid + consistent + exactly the latest frozen revision, `PLAN_DRIFT` instead of freezing an unreviewed edit, `PLAN_MISSING`, `PLAN_NOT_APPROVED`; approval validates then freezes; gate runs in standard / web / handoff launch, foreground + its successor helper, and every NEW run (resume untouched) | `sync.py`, `bt_plan_adapter.py`, `bt_launch.py`, `bt_orchestration_transition.py`, `bt_run.py`, `bt_rounds.py`, `bt_cli_plan.py` (`bind`, `report`) |
| Classification | Schema 1.1.0: `classification_evidence` per dimension (justification ≥ 4 words, typed references, `file:` verified against registered repositories); confidence/assumption rule; coupling must name what it couples to; unordered tasks sharing a path/resource cannot be `coupling: low`; trivial commands, placeholder criteria and repeated text rejected; 1.0.0 still loads | `evidence.py`, `quality.py`, `contract.py`, `data/plan.schema.json`, `data/plan.example.json` |
| Docs | README (contract, agreement table, evidence rules, launch gate, codes), `plan-contract.md`, `requirements.md`, `PLAN-SUPERIA-FASE-1-PLANES.md` §16, D-021, PENDING (P-019 closed, P-023/024/025) | — |

Restrictions kept: `bt_scheduler_core`, `bt_scheduler_adapter.py` and its tests are another session's untracked work and were
only read (the core's `load_plan` loads a 1.1.0 frozen revision); no `RUN.json` touched (sentinel + historical byte
checks); frozen REQ-009/010 revisions still verify; nothing pushed, published or deployed.

## Real planning trials

Six plans, each written after opening the real repository (trainingapp, metodologia), run by `run_trials.py` with
`file:` evidence verified against the checkouts at their current HEAD (`RESULTS.json` records it): **182 / 182 checks**.

| Trial | Intent | What it demonstrated |
|---|---|---|
| TRAIN-1 session expiry | sensitive small fix | real finding (sessions never expire server-side); `complexity low / risk high / isolated_fix`, tests-first chain |
| TRAIN-2 package scope | mechanical large change | plan covers all 9 files a real `grep` finds (incl. Dockerfile); the rename tasks had to be ordered (shared package scope) |
| TRAIN-3 list contract | cross-contract, unknown consumer | research task first, `confidence: low` kept, `high/high/high` change after its schema |
| METH-4 plan quality in review | new feature (dogfood, P-021) | chain terminal → web → docs; legacy page must render unchanged |
| METH-5 relay test wait | investigation | two low-confidence tasks, no invented precision; commands checked to exist |
| TRAIN-6 PostgreSQL migration | system level | a lone `full_system` task refused; exception publishes with a review warning; 6-task decomposition accepted |

Each trial: gate with real evidence → quality judge (critical path, independent dimensions, commands exist, paths
exist or are created, no floating task, real references covered) → 9–10 corruptions each refused with the cause →
approve → freeze → gate → edit = `PLAN_DRIFT` → re-approve r2 (r1 recoverable) → sentinel `RUN.json` byte-identical →
scheduler-core reader loads the frozen revision.

**Defects the trials exposed and fixed:** a stated `verify:` in my own PLAN.md differed from PLAN.json (caught only
because of the new comparison); the 5-word justification floor rejected honest one-line justifications for trivial tasks
(lowered to 4; plans improved); consistency was skipped while schema errors existed, hiding a contradiction behind a
lint (both layers always run); a robustness test found an unhashable `after` crash; the first graph lints were
recursive/quadratic (now iterative bitsets, 2500-task chain passes); a launch before `clone_missing` would have judged
file evidence against an uncloned checkout (unresolved repositories are reported as unverified, not failed); a
milestone heading repeated with the same title is legitimate (supervisor reads last wins) so only differing titles
are ambiguity.

## Verification

Final runs of this session (2026-10-14, after the last code change):

| Suite | Result |
|---|---|
| Module `bt_planner/tests` (normal and `python -I`, includes the isolated lone-copy run and the six scenarios) | 196 tests OK, both |
| Methodology `tests` (includes packaging and `test_plan_integration` 45) | 801 tests OK |
| Scheduler core `bt_scheduler_core/tests` (not modified; run only to prove it is unaffected) | 234 tests OK |
| `run_trials.py` against the real repositories | 182/182 checks |
| Baseline before this requirement | module 111, methodology 752 (REQ-010 report) |

Not run / not claimed: provider-dependent live suites and the Windows/macOS packaging matrix (deferred by the owner).
Independent audit: two fresh reviewer agents (spec, standards) plus a re-verification pass, all findings fixed (below);
they are same-provider reviewers, not another vendor's.

## Independent audit (two fresh reviewers, spec and standards axes)

Both returned CHANGES_NEEDED on the first pass; every verified finding was fixed with a regression test:

| Finding | Fix |
|---|---|
| `file:` evidence accepted unverified when the repo could not be resolved | error at approval and launch (`verify_files`); warning only for a plain `check`; launch gate now runs after the repositories exist |
| `file:*` / `file:.` always "existed" | concrete path required (syntax) and empty static prefix never exists |
| garbage justification / unshaped `command:` `precedent:` `spec:` passed | `command: cmd -> seen`, `precedent` id/commit/URL, `spec` anchor must match a heading and an unanchored spec is context not support; unrelated justification warns |
| RESUMED run never gated | `resume_problem`: not rewritten, but refuses unapproved/invalid PLAN.json when frozen revisions or `plan_ref` exist |
| PLAN.md `files:`/`resources:` never compared | stated entries must appear in `expected_paths`/`shared_resources` |
| misspelt fields and near-miss task ids silently dropped | reported with line |
| JSON duplicate ids without positions | `tasks[i]` positions |
| freeze happened before repo checks | moved after them |
| canonicalisation changed hashes of nested 1.0.0 data (high) | 1.0.0 keeps the exact legacy serialisation; compared byte for byte with the previous implementation |
| exceptions escaping `check`/gate on malformed types, NUL in paths | type guards, NUL rejected, gate fails closed (`PLAN_CHECK_FAILED`); exhaustive fuzz (every position of a real plan × 11 junk values × 2 modes) finds 0 escapes |
| quadratic `<!--` parsing (12 s at 80 KB) | linear scan |
| `echo ok && pytest -q` flagged "cannot fail" | only a pure no-op is trivial |
| CJK criteria rejected by word count | length-based count for unspaced scripts |

Second independent pass (fresh reviewer, items 1–7 re-attacked): all confirmed fixed; it found four more, fixed with tests: resume with PLAN.json deleted after a freeze (now PLAN_MISSING), foreground froze before the workspace check (moved after it), resume demanded file evidence (a resume only verifies existence/validity/latest revision: the run's own work may move files), `T3.1.2` / `**T3**` / `T3 foo` task lines silently ignored (reported). One serialisation nit (a task without `verification` omitted the empty list) restored for byte parity with the old writer.

Not changed on purpose: `--force` of an unapproved plan with nothing frozen freezes it (owner's explicit launch,
recorded `launch-forced`); `in-progress` is a SPEC status, no flow sets it on PLAN.md.

## Limitations (demonstrated)

- Evidence is judged by structure and existence, not truth: a fluent but false justification passes (P-023).
- Hand-edited `status: approved` has no approval record; first launch freezes what it validates, now recorded as `source: launch` in the manifest (P-025 keeps the digest-hook idea).
- The ten-corruption battery and expectations (`EXPECT.json`) were written by the same planner (me); they are regression
  guards, not an independent oracle. The independent reviewers were same-provider agents; a cross-provider `bitacora review` remains open (Proposals).
- Another session's `test_scheduler_integration` errored once in one earlier full run while its adapter was being
  edited; the three later full runs (final: 801 OK) were clean.

## Proposals (not done)
1. Independent audit of REQ-012 by another provider (`bitacora review`) before the Scheduler consumes 1.1.0.
2. P-023 calibration of evidence rules / optional model-assisted review; P-025 approval record for manual approvals.
3. Show `report` in the web plan review (P-021) — METH-4 is a ready plan for it.
